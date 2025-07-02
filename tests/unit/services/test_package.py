from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml
from sdkcraft.services.package import datetime_as_utc_str

DEFAULT_METADATA = {
    "name": "default",
    "title": "default title",
    "base": "ubuntu@22.04",
    "version": "1.0",
    "summary": "default project",
    "license": "MIT",
    "description": "default project",
    "contact": "requests@canonical.com",
    "issues": "https://github.com/canonical/sdks/issues",
    "source-code": "https://github.com/canonical/sdks/",
    "plugs": {"mount": {"interface": "mount", "workshop-target": "/path"}},
    "sdkcraft-started-at": "1970-01-01T00:00:00Z",
}


def test_default_metadata(package_service):
    assert package_service.metadata.marshal() == DEFAULT_METADATA


def test_write_metadata(new_path, package_service, tmp_path_factory):
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

    package_service.write_metadata(prime_dir)

    def contents(path):
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
    assert metadata == DEFAULT_METADATA

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
def test_datetime_as_utc_str(dt, utc):
    assert datetime_as_utc_str(dt) == utc


def test_datetime_as_utc_str_rejects_naive():
    with pytest.raises(NotImplementedError, match="timezone required"):
        datetime_as_utc_str(datetime(2006, 1, 2, 15, 4, 5))
