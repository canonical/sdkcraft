# This file is part of sdkcraft.
#
# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
"""SDKcraft provider service."""

from __future__ import annotations

import logging
import shlex
from itertools import count
from subprocess import CalledProcessError
from typing import override

import yaml
from craft_application import services
from craft_providers import lxd
from craft_providers.errors import details_from_called_process_error
from craft_providers.lxd.lxc import load_yaml_list

logger = logging.getLogger(__name__)


class LXC(lxd.LXC):
    """Wrapper for lxc command-line interface."""

    def storage_create(self, *, name: str, driver: str, remote: str = "local") -> None:
        """Create storage pool.

        :param name: Name of storage pool to create.
        :param driver: Name of storage driver to use.
        :param remote: Name of LXD remote to create pool on.

        :raises LXDError: on unexpected error.
        """
        command = ["storage", "create", f"{remote}:{name}", driver]

        try:
            self._run_lxc(command, capture_output=True)
        except CalledProcessError as error:
            # Handle the race condition where two processes check and
            # create the same storage pool at the same time.
            if name in self.storage_list(remote=remote):
                logger.debug(
                    "Storage pool %s is present on second check, ignoring exception %s.",
                    name,
                    str(error),
                )
            else:
                raise lxd.LXDError(
                    brief=f"Failed to create storage pool {name!r}.",
                    details=details_from_called_process_error(error),
                ) from error

    def storage_list(self, remote: str = "local") -> list[str]:
        """Get list of storage pools.

        :param remote: Name of LXD remote to query.

        :returns: List of storage pool names.

        :raises LXDError: on unexpected error.
        """
        command = ["storage", "list", f"{remote}:", "--format=yaml"]

        try:
            proc = self._run_lxc(command, capture_output=True, text=True)
        except CalledProcessError as error:
            raise lxd.LXDError(
                brief=f"Failed to list storage pools on remote {remote!r}.",
                details=details_from_called_process_error(error),
            ) from error

        try:
            pools = load_yaml_list(proc.stdout)
            return sorted(p["name"] for p in pools)
        except (KeyError, yaml.YAMLError) as error:
            raise lxd.LXDError(
                brief="Failed to parse lxc storage list.",
                details=(
                    f"* Command that failed: {shlex.join(proc.args)!r}\n"
                    f"* Command output: {proc.stdout!r}"
                ),
            ) from error

    def network_create(self, *, name: str, remote: str = "local") -> None:
        """Create new network.

        :param name: Name of network to create.
        :param remote: Name of LXD remote to create network on.

        :raises LXDError: on unexpected error.
        """
        command = ["network", "create", f"{remote}:{name}"]

        try:
            self._run_lxc(command, capture_output=True)
        except CalledProcessError as error:
            # Handle the race condition where two processes check and
            # create the same network at the same time.
            if name in self.network_list(managed=True, remote=remote):
                logger.debug(
                    "Network %s is present on second check, ignoring exception %s.",
                    name,
                    str(error),
                )
            else:
                raise lxd.LXDError(
                    brief=f"Failed to create network {name!r}.",
                    details=details_from_called_process_error(error),
                ) from error

    def network_list(
        self, *, managed: bool | None = None, remote: str = "local"
    ) -> list[str]:
        """Get list of networks.

        :param managed: If set, return only (un)managed networks.
        :param remote: Name of LXD remote to query.

        :returns: List of network names.

        :raises LXDError: on unexpected error.
        """
        command = ["network", "list", f"{remote}:", "--format=yaml"]

        try:
            proc = self._run_lxc(command, capture_output=True, text=True)
        except CalledProcessError as error:
            raise lxd.LXDError(
                brief=f"Failed to list networks on remote {remote!r}.",
                details=details_from_called_process_error(error),
            ) from error

        try:
            networks = load_yaml_list(proc.stdout)
            return sorted(
                n["name"]
                for n in networks
                if managed is None or yaml.safe_load(n.get("managed", "")) == managed
            )
        except (KeyError, yaml.YAMLError) as error:
            raise lxd.LXDError(
                brief="Failed to parse lxc network list.",
                details=(
                    f"* Command that failed: {shlex.join(proc.args)!r}\n"
                    f"* Command output: {proc.stdout!r}"
                ),
            ) from error


def _is_root_disk(device: dict[str, str]) -> bool:
    return (
        device.get("type", "") == "disk"
        and device.get("path", "") == "/"
        and device.get("source", "") == ""
    )


def _create_network(*, remote: str, lxc: LXC) -> str:
    ifaces = lxc.network_list(remote=remote)
    for i in count():
        network = f"lxdbr{i}"
        if network not in ifaces:
            lxc.network_create(name=network, remote=remote)
            return network

    raise AssertionError("infinite loop broken")


def _ensure_storage_and_network(
    *, profile: str = "default", project: str = "default", remote: str = "local"
) -> None:
    """Initialize LXD even if Workshop has already configured it.

    Normally `lxd init --auto` has no effect if a storage pool and a network
    already exist. Since Workshop creates its own, we create the default ones
    manually here. This needs to happen before ensure_lxd_is_ready() is called.
    """
    lxc = LXC()

    config = lxc.profile_show(profile=profile, project=project, remote=remote)
    devices = config.setdefault("devices", {})

    if not any(_is_root_disk(d) for d in devices.values()):
        if "root" in devices:
            raise lxd.LXDError(
                brief=f"Cannot add 'root' device to {profile!r} profile: already exists."
            )

        if "default" not in lxc.storage_list(remote=remote):
            lxc.storage_create(name="default", driver="dir", remote=remote)

        devices["root"] = {"path": "/", "pool": "default", "type": "disk"}

    if not any(d.get("type", "") == "nic" for d in devices.values()):
        if "eth0" in devices:
            raise lxd.LXDError(
                brief="Cannot add 'eth0' device to {profile!r} profile: already exists."
            )

        network = "lxdbr0"
        if network not in lxc.network_list(managed=True, remote=remote):
            network = _create_network(remote=remote, lxc=lxc)

        devices["eth0"] = {"name": "eth0", "network": network, "type": "nic"}

    lxc.profile_edit(profile="default", config=config, project=project, remote=remote)


class LXDProvider(lxd.LXDProvider):
    """LXD build environment provider."""

    @override
    @classmethod
    def ensure_provider_is_available(cls) -> None:
        """Ensure provider is available and ready, installing if required.

        :raises LXDInstallationError: if LXD cannot be installed
        :raises LXDError: if provider is not available
        """
        if not lxd.is_installed():
            lxd.install()
        _ensure_storage_and_network()
        lxd.ensure_lxd_is_ready()


class ProviderService(services.ProviderService):
    """Manager for craft_providers in an SDKcraft."""

    @override
    def _get_lxd_provider(self) -> LXDProvider:
        """Get the LXD provider for this manager."""
        lxd_remote = self._services.config.get("lxd_remote")
        return LXDProvider(lxd_project=self._app.name, lxd_remote=lxd_remote)
