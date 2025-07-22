import stat
import subprocess
import sys
import tarfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest
import sdkcraft.cli
import yaml
from craft_platforms import DebianArchitecture

pytestmark = [pytest.mark.slow, pytest.mark.usefixtures("reset_callbacks")]


@pytest.fixture
def sdk_yaml_template() -> str:
    return """\
name: my-project
title: My Project
version: 1.2.3
base: ubuntu@22.04
build-base: "ubuntu@RELEASE_VERSION"
summary: "example of global variables"
description: "example of global variables"
license: Apache-2.0
platforms:
  DEBIAN_ARCH:

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


@pytest.fixture
def sdk_yaml(sdk_yaml_template: str, release_version: str) -> str:
    arch = str(DebianArchitecture.from_host())
    replacements = {
        "RELEASE_VERSION": release_version,
        "DEBIAN_ARCH": arch,
    }

    result = sdk_yaml_template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def test_global_environment(
    new_path: Path,
    sdk_yaml: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test our additions to the global environment that is available to the
    build process."""

    Path("sdk.yaml").write_text(sdk_yaml)

    monkeypatch.setattr(sys, "argv", ["sdkcraft", "prime", "--destructive-mode"])

    return_code = sdkcraft.cli.main()
    assert return_code == 0

    variables_yaml = new_path / "stage" / "variables.yaml"
    assert variables_yaml.is_file()
    variables = yaml.safe_load(variables_yaml.read_text())

    assert variables["project_name"] == "my-project"
    assert variables["project_dir"] == str(new_path)
    assert variables["project_version"] == "1.2.3"


def test_pack(
    new_path: Path,
    sdk_yaml: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test packed SDK contents."""

    Path("sdk.yaml").write_text(sdk_yaml)
    Path("hooks").mkdir()
    (Path("hooks") / "setup-base").write_text("touch /etc/fstab\n")
    (Path("hooks") / "setup-base").chmod(stat.S_IRWXU | stat.S_IWGRP | stat.S_IROTH)

    monkeypatch.setattr(sys, "argv", ["sdkcraft", "pack", "--destructive-mode"])

    return_code = sdkcraft.cli.main()
    assert return_code == 0

    arch = DebianArchitecture.from_host()
    filename = f"my-project_{arch}_ubuntu@22.04.sdk"

    subprocess.run(
        ["zstd", "--decompress", "-o", "my-project.tar", filename],
        check=True,
        cwd=new_path,
    )

    with tarfile.open(new_path / "my-project.tar") as tar:
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

        meta_sdk_yaml = tar.extractfile("meta/sdk.yaml")
        assert meta_sdk_yaml is not None
        with meta_sdk_yaml:
            metadata = yaml.safe_load(meta_sdk_yaml)
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
        assert info.mode == stat.S_IRWXU | stat.S_IROTH
        assert info.uid == 0
        assert info.gid == 0
        assert info.uname == "root"
        assert info.gname == "root"

        setup_base = tar.extractfile(info)
        assert setup_base is not None
        with setup_base:
            assert setup_base.read() == b"touch /etc/fstab\n"


@pytest.mark.parametrize(
    "sdk_yaml_template",
    [
        pytest.param(
            """\
name: my-project
version: 1.2.3
build-base: ubuntu@RELEASE_VERSION
platforms:
  DEBIAN_ARCH:
""",
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_pack_base_agnostic(
    new_path: Path,
    sdk_yaml: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test packed SDK contents."""

    Path("sdk.yaml").write_text(sdk_yaml)

    monkeypatch.setattr(sys, "argv", ["sdkcraft", "pack", "--destructive-mode"])

    return_code = sdkcraft.cli.main()
    assert return_code == 0

    files = sorted(path.name for path in new_path.glob("*.sdk"))
    arch = DebianArchitecture.from_host()
    assert files == [f"my-project_{arch}.sdk"]


@pytest.mark.parametrize(
    "sdk_yaml_template",
    [
        pytest.param(
            """\
name: my-project
version: 1.2.3
base: ubuntu@RELEASE_VERSION
platforms:
  all:
    build-on: DEBIAN_ARCH
    build-for: all
""",
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_pack_architecture_agnostic(
    new_path: Path,
    release_version: str,
    sdk_yaml: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test packed SDK contents."""

    Path("sdk.yaml").write_text(sdk_yaml)

    monkeypatch.setattr(sys, "argv", ["sdkcraft", "pack", "--destructive-mode"])

    return_code = sdkcraft.cli.main()
    assert return_code == 0

    files = sorted(path.name for path in new_path.glob("*.sdk"))
    assert files == [f"my-project_all_ubuntu@{release_version}.sdk"]
