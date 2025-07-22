from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml
from craft_platforms import DebianArchitecture
from sdkcraft.services.package import PackageService, datetime_as_utc_str

DEFAULT_METADATA = {
    "name": "default",
    "title": "default title",
    "version": "1.0",
    "summary": "default project",
    "description": "default project",
    "base": "ubuntu@22.04",
    "contact": "requests@canonical.com",
    "issues": "https://github.com/canonical/sdks/issues",
    "source-code": "https://github.com/canonical/sdks",
    "license": "MIT",
    "plugs": {"mount": {"interface": "mount", "workshop-target": "/path"}},
    "sdkcraft-started-at": "1970-01-01T00:00:00Z",
}


def test_default_metadata(
    fake_arch: DebianArchitecture,
    package_service_with_configured_project: PackageService,
):
    default_metadata = DEFAULT_METADATA | {"architecture": str(fake_arch)}
    assert (
        package_service_with_configured_project.metadata.marshal() == default_metadata
    )


@pytest.mark.parametrize(
    ("fake_arch_str", "project_data"),
    [
        pytest.param(
            "s390x",
            {
                "name": "build-base-metadata",
                "version": "1.0",
                "build-base": "ubuntu@20.04",
                "platforms": {
                    "all": {
                        "build-on": ["amd64", "s390x"],
                        "build-for": "all",
                    },
                },
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_build_base_metadata(
    fake_arch: DebianArchitecture,
    package_service_with_configured_project: PackageService,
):
    _ = fake_arch
    metadata = {
        "name": "build-base-metadata",
        "version": "1.0",
        "architecture": "all",
        "sdkcraft-started-at": "1970-01-01T00:00:00Z",
    }
    assert package_service_with_configured_project.metadata.marshal() == metadata


def test_write_metadata(
    new_path: Path,
    fake_arch: DebianArchitecture,
    package_service_with_configured_project: PackageService,
    tmp_path_factory: pytest.TempPathFactory,
):
    prime_dir = tmp_path_factory.mktemp("prime")
    hooks_dir = prime_dir / "sdk" / "hooks"
    hooks_dir.parent.mkdir()
    hooks_dir.mkdir()
    (hooks_dir / "setup-base").write_text("echo old\n")
    (hooks_dir / "check-health").write_text("workshopctl set-health okay\n")

    (new_path / "hooks").mkdir()
    (new_path / "hooks" / "utils.sh").write_text("message() { echo new; }\n")
    (new_path / "hooks" / "link").symlink_to("/x/y/z")
    (new_path / "hooks" / "setup-base").write_text(". utils.sh\nmessage\n")

    package_service_with_configured_project.write_metadata(prime_dir)

    def contents(path: Path) -> Path | set[str] | str:
        if path.is_symlink():
            return path.readlink()
        if path.is_dir():
            return {p.name for p in path.iterdir()}
        return path.read_text()

    assert contents(prime_dir) == {"meta", "sdk"}
    assert contents(prime_dir / "meta") == {"sdk.yaml"}
    assert contents(prime_dir / "sdk") == {"hooks"}
    assert contents(hooks_dir) == {"setup-base", "link", "utils.sh"}

    with (prime_dir / "meta" / "sdk.yaml").open() as f:
        metadata = yaml.safe_load(f)

    default_metadata = DEFAULT_METADATA | {"architecture": str(fake_arch)}
    assert metadata == default_metadata

    assert contents(hooks_dir / "setup-base") == ". utils.sh\nmessage\n"
    assert contents(hooks_dir / "link") == Path("/x/y/z")
    assert contents(hooks_dir / "utils.sh") == "message() { echo new; }\n"


@pytest.mark.parametrize(
    ("dt", "utc"),
    [
        (
            datetime.fromtimestamp(0, timezone.utc),
            "1970-01-01T00:00:00Z",
        ),
        (
            datetime(2006, 1, 2, 15, 4, 5, 8, timezone(timedelta(hours=-7))),
            "2006-01-02T22:04:05.000008Z",
        ),
    ],
)
def test_datetime_as_utc_str(dt: datetime, utc: timezone):
    assert datetime_as_utc_str(dt) == utc


def test_datetime_as_utc_str_rejects_naive():
    with pytest.raises(NotImplementedError, match="timezone required"):
        datetime_as_utc_str(datetime(2006, 1, 2, 15, 4, 5))
