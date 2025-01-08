import pytest


@pytest.mark.parametrize(
    ("expected"),
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
            "issues": "https://github.com/canonical/sdk-store/issues",
            "source-code": "https://github.com/canonical/sdk-store/",
            "plugs": {"content": {"target": "/path"}},
            "sdkcraft-started-at": "1970-01-01T00:00:00+00:00",
        },
    ],
)
def test_pack_default_metadata(package_service, expected):
    assert package_service.metadata.marshal() == expected
