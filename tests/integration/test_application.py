import stat
import sys
import tarfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest
import yaml
from craft_parts import errors
from craft_parts.utils import os_utils
from sdkcraft.application import APP_METADATA, Sdkcraft
from sdkcraft.services import Lifecycle, Package, ServiceFactory


def is_ubuntu_jammy() -> bool:
    release = os_utils.OsRelease()
    try:
        return release.id() == "ubuntu" and release.version_id() == "22.04"
    except errors.OsReleaseIdError:
        return False


jammy_only = pytest.mark.skipif(
    not is_ubuntu_jammy(), reason="platform must be Ubuntu Jammy"
)

pytestmark = [pytest.mark.usefixtures("_reset_callbacks")]


def get_sdk_yaml_string(release_version: str) -> str:
    return (
        """\
name: my-project
title: My Project
version: 1.2.3
base: ubuntu@22.04
build-base: "ubuntu@RELEASE_VERSION"
summary: "example of global variables"
description: "example of global variables"
license: Apache-2.0
platforms:
  amd64:

parts:
  foo:
    plugin: nil
    override-build: |
      target_file=${CRAFT_PART_INSTALL}/variables.yaml
      touch $target_file
      echo "project_name:    \\"${CRAFT_PROJECT_NAME}\\""    >> $target_file
      echo "project_dir:     \\"${CRAFT_PROJECT_DIR}\\""     >> $target_file
      echo "project_version: \\"${CRAFT_PROJECT_VERSION}\\"" >> $target_file
"""
    ).replace("RELEASE_VERSION", release_version, 1)


@pytest.mark.slow
def test_global_environment(
    new_path,
    release_version,
    monkeypatch,
):
    """Test our additions to the global environment that is available to the
    build process."""

    Path("sdk.yaml").write_text(get_sdk_yaml_string(release_version))

    monkeypatch.setattr(sys, "argv", ["sdkcraft", "prime", "--destructive-mode"])

    ServiceFactory.register("package", Package)
    ServiceFactory.register("lifecycle", Lifecycle)

    service = ServiceFactory(
        app=APP_METADATA,
    )

    app = Sdkcraft(app=APP_METADATA, services=service)
    app.run()

    variables_yaml = new_path / "stage" / "variables.yaml"
    assert variables_yaml.is_file()
    variables = yaml.safe_load(variables_yaml.read_text())

    assert variables["project_name"] == "my-project"
    assert variables["project_dir"] == str(new_path)
    assert variables["project_version"] == "1.2.3"


@pytest.mark.slow
def test_pack(
    new_path,
    release_version,
    monkeypatch,
):
    """Test our additions to the global environment that is available to the
    build process."""

    Path("sdk.yaml").write_text(get_sdk_yaml_string(release_version))
    Path("hooks").mkdir()
    (Path("hooks") / "setup-base").write_text("touch /etc/fstab\n")
    (Path("hooks") / "setup-base").chmod(stat.S_IRWXU | stat.S_IWGRP | stat.S_IROTH)

    monkeypatch.setattr(sys, "argv", ["sdkcraft", "pack", "--destructive-mode"])

    ServiceFactory.register("package", Package)
    ServiceFactory.register("lifecycle", Lifecycle)

    service = ServiceFactory(
        app=APP_METADATA,
    )

    app = Sdkcraft(app=APP_METADATA, services=service)
    app.run()

    with tarfile.open(new_path / "my-project.sdk") as tar:
        members = Counter(member.name for member in tar)
        assert set(members.keys()) == {
            "meta",
            "meta/sdk.yaml",
            "sdk",
            "sdk/hooks",
            "sdk/hooks/setup-base",
            "variables.yaml",
        }
        assert set(members.values()) == {1}

        sdk_yaml = tar.extractfile("meta/sdk.yaml")
        assert sdk_yaml is not None
        with sdk_yaml:
            metadata = yaml.safe_load(sdk_yaml)
        assert metadata["name"] == "my-project"
        assert metadata["title"] == "My Project"
        assert metadata["version"] == "1.2.3"
        assert "platforms" not in metadata
        assert "parts" not in metadata

        started_at_str = metadata["sdkcraft-started-at"]
        if sys.version_info < (3, 11) and started_at_str.endswith("Z"):
            started_at_str = started_at_str[:-1] + "+00:00"
        started_at = datetime.fromisoformat(started_at_str)

        info = tar.getmember("sdk/hooks/setup-base")
        assert info.mtime == pytest.approx(started_at.timestamp(), abs=2.0)
        assert info.mode == stat.S_IRWXU | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
        assert info.uid == 0
        assert info.gid == 0
        assert info.uname == "root"
        assert info.gname == "root"

        setup_base = tar.extractfile(info)
        assert setup_base is not None
        with setup_base:
            assert setup_base.read() == b"touch /etc/fstab\n"
