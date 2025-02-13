from datetime import datetime, timedelta, timezone

import pytest
from sdkcraft.services.package import datetime_as_utc_str


@pytest.mark.parametrize(
    "expected",
    [
        {
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
            "plugs": {"content": {"target": "/path"}},
            "sdkcraft-started-at": "1970-01-01T00:00:00Z",
        },
    ],
)
def test_pack_default_metadata(package_service, expected):
    assert package_service.metadata.marshal() == expected


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
