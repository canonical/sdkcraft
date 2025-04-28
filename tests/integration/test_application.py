import sys
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
    new_dir,
    release_version,
    monkeypatch,
):
    """Test our additions to the global environment that is available to the
    build process."""

    rootfs = Path(new_dir) / "rootfs"
    rootfs.mkdir()

    Path("sdk.yaml").write_text(get_sdk_yaml_string(release_version))

    monkeypatch.setattr(sys, "argv", ["sdkcraft", "prime", "--destructive-mode"])

    ServiceFactory.register("package", Package)
    ServiceFactory.register("lifecycle", Lifecycle)

    service = ServiceFactory(
        # type: ignore[call-arg]
        app=APP_METADATA,
    )

    app = Sdkcraft(app=APP_METADATA, services=service)
    app.run()

    variables_yaml = Path(new_dir) / "stage" / "variables.yaml"
    assert variables_yaml.is_file()
    variables = yaml.safe_load(variables_yaml.read_text())

    assert variables["project_name"] == "my-project"
    assert variables["project_dir"] == str(new_dir)
    assert variables["project_version"] == "1.2.3"
