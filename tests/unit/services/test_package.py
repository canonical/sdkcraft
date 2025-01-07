import pytest


@pytest.mark.parametrize(
    ("expected"),
    [
        {
            "name": "default",
            "title": "default title",
            "base": "ubuntu@22.04",
            "summary": "default project",
            "license": "MIT",
            "description": "default project",
            "contact": "requests@canonical.com",
            "issues": "https://github.com/canonical/sdk-store/issues",
            'source-code': 'https://github.com/canonical/sdk-store/',
            "plugs": {"content": {"target": "/path"}},
        },
    ],
)
def test_pack_default_metadata(package_service, expected):
    assert package_service.metadata.marshal() == expected
