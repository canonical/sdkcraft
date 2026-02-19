from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess
from typing import TYPE_CHECKING, Any

import pytest
from craft_application.util import safe_yaml_load
from sdkcraft.services.testing import SPREAD_PREPARE, SPREAD_PREPARE_SEP, TestingService

if TYPE_CHECKING:
    from craft_platforms import DebianArchitecture
    from pytest_mock import MockerFixture, MockType

pytestmark = pytest.mark.usefixtures("configure_project")


@pytest.fixture(autouse=True)
def fake_which(mocker: MockerFixture) -> MockType:
    return mocker.patch("shutil.which", return_value="/fake-bin/craft.spread")


@pytest.fixture
def spread_list() -> str:
    return """\
lxd:ubuntu-24.04:main/launch:jammy
lxd:ubuntu-24.04:main/launch:noble
lxd:ubuntu-24.04:main/launch:other
lxd:ubuntu-24.04:main/refresh
"""


@pytest.fixture(autouse=True)
def fake_run(
    fake_arch: DebianArchitecture, mocker: MockerFixture, spread_list: str
) -> MockType:
    # We don't use fake_arch here, but it needs to run first because
    # platform.uname can shell out to the `uname` command.
    _ = fake_arch

    def side_effect(
        cmd: list[str], *_args: Any, **_kwargs: Any
    ) -> CompletedProcess[str]:
        result = CompletedProcess[str](cmd, 0)
        if cmd[:2] == ["/fake-bin/craft.spread", "-list"]:
            result.stdout = spread_list
        return result

    return mocker.patch("subprocess.run", side_effect=side_effect)


@pytest.fixture(autouse=True)
def fake_popen(fake_arch: DebianArchitecture, mocker: MockerFixture) -> MockType:
    # We don't use fake_arch here, but it needs to run first because
    # platform.uname can shell out to the `uname` command.
    _ = fake_arch

    process = mocker.MagicMock()
    process.__enter__.return_value = process
    process.__exit__.return_value = None
    process.wait.return_value = None
    process.poll.return_value = 0

    spread_paths = []
    spread_projects = []

    def side_effect(cmd: list[str], *_args: Any, cwd: Path, **_kwargs: Any) -> MockType:
        if cmd[:1] == ["/fake-bin/craft.spread"]:
            with (cwd / "spread.yaml").open() as f:
                spread_paths.append(cwd)
                spread_projects.append(safe_yaml_load(f))
        return process

    return mocker.patch(
        "subprocess.Popen",
        side_effect=side_effect,
        spread_paths=spread_paths,
        spread_projects=spread_projects,
    )


def test_spread_arguments(
    testing_service: TestingService,
    fake_try_service: dict[str, MockType],
    tmp_path: Path,
    fake_popen: MockType,
):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "spread.yaml").write_text("{}")

    artifacts = {"ppc64el": Path("default_ppc64el_ubuntu@22.04.sdk")}
    testing_service.sdkcraft_test(
        tmp_path,
        artifacts,
        bases=["ubuntu@22.04"],
        shell_after=True,
    )

    craft_spread = fake_popen.call_args.kwargs["cwd"]
    assert craft_spread.parent == tmp_path / "tests"
    assert craft_spread.name.startswith(".craft-spread-")

    fake_try_service["copy"].assert_called_once_with(
        "default", artifacts, craft_spread / "try"
    )
    fake_popen.assert_called_once_with(
        [
            "/fake-bin/craft.spread",
            "-reuse",
            "-resend",
            "-shell-after",
            "lxd:ubuntu-24.04:main/launch:jammy",
            "lxd:ubuntu-24.04:main/launch:other",
            "lxd:ubuntu-24.04:main/refresh",
        ],
        cwd=craft_spread,
    )


@pytest.mark.usefixtures("fake_try_service")
def test_spread_build_base_only(
    testing_service: TestingService,
    tmp_path: Path,
    fake_popen: MockType,
):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "spread.yaml").write_text("{}")

    artifacts = {"ppc64el": Path("default_ppc64el_ubuntu@22.04.sdk")}
    testing_service.sdkcraft_test(
        tmp_path,
        artifacts,
        bases=[None],
        debug=True,
    )

    craft_spread = fake_popen.call_args.kwargs["cwd"]
    fake_popen.assert_called_once_with(
        [
            "/fake-bin/craft.spread",
            "-reuse",
            "-resend",
            "-debug",
            "lxd:ubuntu-24.04:main/launch:jammy",
            "lxd:ubuntu-24.04:main/launch:noble",
            "lxd:ubuntu-24.04:main/launch:other",
            "lxd:ubuntu-24.04:main/refresh",
        ],
        cwd=craft_spread,
    )


@pytest.mark.usefixtures("fake_try_service")
def test_spread_yaml(
    testing_service: TestingService,
    tmp_path: Path,
    fake_popen: MockType,
):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "spread.yaml").write_text("{}")

    artifacts = {"ppc64el": Path("default_ppc64el_ubuntu@22.04.sdk")}
    testing_service.sdkcraft_test(tmp_path, artifacts)

    assert fake_popen.spread_paths[0].parent == tmp_path / "tests"
    prepare = SPREAD_PREPARE.replace("TEMPNAME", fake_popen.spread_paths[0].name)
    projects = [{"reroot": "..", "prepare": prepare}]
    assert fake_popen.spread_projects == projects

    (tmp_path / "tests" / "spread.yaml").write_text("""\
reroot: ..
prepare: |
  sudo apt-get update
  sudo apt-get install build-essential
""")

    testing_service.sdkcraft_test(tmp_path, artifacts)

    assert fake_popen.spread_paths[1].parent == tmp_path
    prepare = SPREAD_PREPARE.replace("TEMPNAME", fake_popen.spread_paths[1].name)
    prepare += SPREAD_PREPARE_SEP
    prepare += """\
sudo apt-get update
sudo apt-get install build-essential
"""
    projects.append({"reroot": "..", "prepare": prepare})
    assert fake_popen.spread_projects == projects


def test_spread_discard(
    testing_service: TestingService,
    tmp_path: Path,
    fake_run: MockType,
):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "spread.yaml").write_text("reroot: ..\n")
    (tmp_path / ".craft-spread-abcxyz").mkdir()

    testing_service.clean(tmp_path)

    stdout = fake_run.call_args.kwargs["stdout"]
    stderr = fake_run.call_args.kwargs["stderr"]

    fake_run.assert_called_once_with(
        ["/fake-bin/craft.spread", "-discard"],
        check=True,
        stdout=stdout,
        stderr=stderr,
        cwd=tmp_path / "tests",
    )

    assert not (tmp_path / ".craft-spread-abcxyz").exists()
