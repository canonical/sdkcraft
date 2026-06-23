#  This file is part of sdkcraft.
#
# Copyright 2024 Canonical Ltd.
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 3, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
#  SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Constrained pydantic types for SDKcraft."""

from __future__ import annotations

import posixpath
import re
from ipaddress import ip_address
from string import Template
from typing import Annotated, Any
from urllib.parse import urlsplit, urlunsplit

from craft_application.models import constraints
from pydantic import AfterValidator, BeforeValidator, Field
from pydantic.fields import FieldInfo

from sdkcraft.dirs import WORKSHOP_SDKS_DIR

RESERVED_NAME_REGEX = r"(?!^(system|try-.*|project-.*|sketch)$)"
RESERVED_NAME_COMPILED_REGEX = re.compile(RESERVED_NAME_REGEX)
MESSAGE_RESERVED_NAME = (
    "invalid name: Names cannot be 'system', 'sketch' or start with 'project-'."
)

PROJECT_NAME_REGEX = RESERVED_NAME_REGEX + constraints.PROJECT_NAME_REGEX
PROJECT_NAME_COMPILED_REGEX = re.compile(PROJECT_NAME_REGEX)

PLUG_NAME_DESCRIPTION = """\
The name of the {0}. This is used when connecting and disconnecting.

The {0} name must consist only of lower-case ASCII letters (``a-z``), numerals
(``0-9``), and hyphens (``-``). It must start with a letter, not end with a
hyphen, and not contain two consecutive hyphens.
"""
PLUG_NAME_REGEX = r"^[a-z](-?[a-z0-9])*$"
PLUG_NAME_COMPILED_REGEX = re.compile(PLUG_NAME_REGEX)
MESSAGE_INVALID_PLUG_NAME = (
    "invalid name: {0} names can only use ASCII lowercase letters, numbers, and hyphens. "
    "They must start with a letter, may not end with a hyphen, "
    "and may not have two hyphens in a row."
)

OCTAL_COMPILED_REGEX = re.compile("0[0-9]")

INVALID_UID = 0xFFFFFFFF
FILE_MODE_MASK = 0o777


type ProjectName = Annotated[
    str,
    Field(pattern=PROJECT_NAME_COMPILED_REGEX),
    FieldInfo.from_annotation(constraints.ProjectName),  # pyright: ignore[reportArgumentType]
    BeforeValidator(
        constraints.get_validator_by_regex(
            RESERVED_NAME_COMPILED_REGEX, MESSAGE_RESERVED_NAME
        )
    ),
]


type PlugName = Annotated[
    str,
    Field(
        strict=True,
        pattern=PLUG_NAME_REGEX,
        description=PLUG_NAME_DESCRIPTION.format("plug"),
        title="Plug Name",
        examples=[
            "desktop",
            "gpu",
            "ssh-agent",
        ],
    ),
    BeforeValidator(
        constraints.get_validator_by_regex(
            PLUG_NAME_COMPILED_REGEX, MESSAGE_INVALID_PLUG_NAME.format("plug")
        )
    ),
]
type SlotName = Annotated[
    str,
    Field(
        strict=True,
        pattern=PLUG_NAME_REGEX,
        description=PLUG_NAME_DESCRIPTION.format("slot"),
        title="Slot Name",
        examples=[
            "dashboard",
            "gdb",
            "toolchain",
        ],
    ),
    BeforeValidator(
        constraints.get_validator_by_regex(
            PLUG_NAME_COMPILED_REGEX, MESSAGE_INVALID_PLUG_NAME.format("slot")
        )
    ),
]


DEVICE_ID_REGEX = r"^(?:0x)?[a-fA-F0-9]+$"
DEVICE_ID_COMPILED_REGEX = re.compile(DEVICE_ID_REGEX)
MESSAGE_INVALID_DEVICE_ID = "invalid device ID: must be a hexadecimal number."


def _check_device_id(device_id: str) -> str:
    if int(device_id, base=16) >= (1 << 16):
        raise ValueError("invalid device ID: maximum is 0xffff")
    return device_id


type DeviceID = Annotated[
    str,
    Field(strict=True, pattern=DEVICE_ID_REGEX),
    BeforeValidator(
        constraints.get_validator_by_regex(
            DEVICE_ID_COMPILED_REGEX, MESSAGE_INVALID_DEVICE_ID
        )
    ),
    AfterValidator(_check_device_id),
]


def _is_clean_abspath(path: str) -> str:
    try:
        expanded = Template(path).substitute(SDK=WORKSHOP_SDKS_DIR / "unknown")
    except KeyError as e:
        key = next(iter(e.args), None)
        suffix = f"in {path!r}" if key is None else f"{key!r}"
        raise ValueError(f"unexpected variable {suffix}")

    if not posixpath.isabs(expanded):
        raise ValueError(f"path {path!r} must be absolute")

    cleaned = posixpath.normpath(expanded)
    if cleaned != expanded:
        raise ValueError(f"path {path!r} should be shortened to {cleaned!r}")

    return path


type CleanAbsPath = Annotated[str, AfterValidator(_is_clean_abspath)]


# Retrieved from https://api.charmhub.io/docs/default.html#create_tracks
# (mirrored by craft_store.publisher._publishergw.TRACK_NAME_REGEX)
TRACK_NAME_REGEX = r"^[a-zA-Z0-9](?:[_.-]?[a-zA-Z0-9])*$"
TRACK_NAME_COMPILED_REGEX = re.compile(TRACK_NAME_REGEX)
TRACK_NAME_MAX_LENGTH = 28


def _check_track_name(name: str) -> str:
    """Validate that *name* is a valid store track name."""
    if len(name) > TRACK_NAME_MAX_LENGTH:
        raise ValueError(
            f"Invalid track name {name!r}: must be at most "
            f"{TRACK_NAME_MAX_LENGTH} characters."
        )
    if not TRACK_NAME_COMPILED_REGEX.match(name):
        raise ValueError(
            f"Invalid track name {name!r}: must start and end with an "
            "alphanumeric character and contain only alphanumeric "
            "characters, hyphens, dots, or underscores."
        )
    return name


type TrackName = Annotated[str, AfterValidator(_check_track_name)]


_CHANNEL_VALID_RISKS = frozenset({"stable", "candidate", "beta", "edge"})


def _check_channel_risk(channel: str) -> str:
    """Validate that *channel* contains a recognized risk level.

    A channel has the form `[<track>/]<risk>[/<branch>]`.
    If a track is present, it is validated against the track name rules.
    """
    parts = channel.split("/")
    track: str | None = None
    if len(parts) == 1:
        risk = parts[0]
    elif len(parts) < 3:  # noqa: PLR2004
        # Either <track>/<risk> or <risk>/<branch>
        if parts[0] in _CHANNEL_VALID_RISKS:
            risk = parts[0]
        else:
            track = parts[0]
            risk = parts[1]
    else:
        # <track>/<risk>/<branch>
        track = parts[0]
        risk = parts[1]

    if risk not in _CHANNEL_VALID_RISKS:
        raise ValueError(
            f"Invalid channel {channel!r}: risk must be one of "
            f"{', '.join(sorted(_CHANNEL_VALID_RISKS))}."
        )

    if track is not None:
        _check_track_name(track)

    return channel


type ChannelName = Annotated[str, AfterValidator(_check_channel_risk)]


def _str_as_int(value: Any) -> Any:  # noqa: ANN401
    if not isinstance(value, str):
        return value

    if OCTAL_COMPILED_REGEX.match(value):
        value = f"0o{value[1:]}"
    return int(value, base=0)


# Python uses YAML 1.1 whereas Go supports a hybrid of 1.1 and 1.2. The main
# difference for us is that PyYAML parses 0o777 as a str, not an int. The
# interface system is lenient about accepting other strings, and so is
# pydantic, but the latter doesn't support binary, hex or octal strings.
# This type accepts both ints and strs, and works like strconv.ParseInt.
type Int = Annotated[int, BeforeValidator(_str_as_int)]


type UserGroupID = Annotated[Int, Field(ge=0, lt=INVALID_UID)]
type FileMode = Annotated[Int, Field(ge=0, le=FILE_MODE_MASK)]


def _parse_netloc(netloc: str) -> tuple[str | None, int | None]:
    split = urlsplit(urlunsplit(("", netloc, "", "", "")))

    if (
        (split.scheme, split.path, split.query, split.fragment) != ("", "", "", "")
        or split.username is not None
        or split.password is not None
    ):
        raise ValueError("expected hostname:port")

    return split.hostname, split.port


def _parse_address(address: str) -> tuple[str, int | None]:
    if not address:
        return "localhost", None

    if address.isdigit():
        hostname, port = _parse_netloc(f"localhost:{address}")
        if hostname != "localhost":
            raise AssertionError("expected digits to parse as port")
        return hostname, port

    try:
        hostname, port = _parse_netloc(address)
    except ValueError:
        pass
    else:
        if hostname is not None and port is not None:
            return hostname, port

    # Remove square brackets from standalone address.
    try:
        hostname, port = _parse_netloc(f"{address}:")
    except ValueError:
        pass
    else:
        if hostname is not None and port is None:
            return hostname, port

    return address, None


def _validate_endpoint(endpoint: str) -> str:
    if endpoint.startswith(("/", "@")):
        return endpoint
    if endpoint.startswith("$"):
        if endpoint.startswith(("$HOME/", "$XDG_RUNTIME_DIR/")):
            return endpoint
        variable, _, _ = endpoint.partition("/")
        raise ValueError(f"unexpected variable {variable!r}")

    if endpoint in ("tcp", "udp"):
        address = ""
    elif endpoint.endswith("/tcp"):
        address = endpoint.removesuffix("/tcp")
    elif endpoint.endswith("/udp"):
        address = endpoint.removesuffix("/udp")
    else:
        address = endpoint

    # Port is unused but still needs to be computed.
    # It is validated when querying the SplitResult.port property.
    hostname, _ = _parse_address(address)

    if hostname not in ("localhost", "ip6-localhost", "ip6-loopback"):
        ip_address(hostname)

    return endpoint


type Endpoint = Annotated[str, AfterValidator(_validate_endpoint)]
