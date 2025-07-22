import pytest
from craft_platforms import (
    AllOnlyBuildError,
    BuildInfo,
    DebianArchitecture,
    DistroBase,
    InvalidMultiBaseError,
    RequiresBaseError,
)
from sdkcraft.errors import RepeatedPlatformError
from sdkcraft.services.buildplan import BuildPlanService


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "no-platforms",
                "platforms": {},
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_no_platforms(build_plan_service: BuildPlanService):
    assert build_plan(build_plan_service) == []


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "no-base-ppc64el",
                "platforms": {"ppc64el": None},
            },
            id="arch_only",
        ),
        pytest.param(
            {
                "name": "multi-base-missing-base",
                "platforms": {"ubuntu@22.04:i386": None, "s390x": None},
            },
            id="multi_base",
        ),
    ],
)
def test_no_base(build_plan_service: BuildPlanService):
    with pytest.raises(RequiresBaseError):
        build_plan(build_plan_service)


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "base-only-ppc64el",
                "base": "distro@series",
                "platforms": {"ppc64el": None},
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_base_only(build_plan_service: BuildPlanService):
    assert build_plan(build_plan_service) == [
        BuildInfo(
            platform="ppc64el",
            build_on=DebianArchitecture.PPC64EL,
            build_for=DebianArchitecture.PPC64EL,
            build_base=DistroBase(distribution="distro", series="series"),
        )
    ]


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "build-base-only-ppc64el",
                "build-base": "distro@series",
                "platforms": {"ppc64el": None},
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_build_base_only(build_plan_service: BuildPlanService):
    assert build_plan(build_plan_service) == [
        BuildInfo(
            platform="ppc64el",
            build_on=DebianArchitecture.PPC64EL,
            build_for=DebianArchitecture.PPC64EL,
            build_base=DistroBase(distribution="distro", series="series"),
        )
    ]


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "base-and-build-base-ppc64el",
                "base": "ubuntu@25.10",
                "build-base": "ubuntu@20.04",
                "platforms": {"ppc64el": None},
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_base_and_build_base(build_plan_service: BuildPlanService):
    assert build_plan(build_plan_service) == [
        BuildInfo(
            platform="ppc64el",
            build_on=DebianArchitecture.PPC64EL,
            build_for=DebianArchitecture.PPC64EL,
            build_base=DistroBase(distribution="ubuntu", series="20.04"),
        )
    ]


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "multi-base-i386-s390x",
                "platforms": {"ubuntu@22.04:i386": None, "ubuntu@24.04:s390x": None},
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_multi_base(build_plan_service: BuildPlanService):
    assert build_plan(build_plan_service) == [
        BuildInfo(
            platform="ubuntu@22.04:i386",
            build_on=DebianArchitecture.I386,
            build_for=DebianArchitecture.I386,
            build_base=DistroBase(distribution="ubuntu", series="22.04"),
        ),
        BuildInfo(
            platform="ubuntu@24.04:s390x",
            build_on=DebianArchitecture.S390X,
            build_for=DebianArchitecture.S390X,
            build_base=DistroBase(distribution="ubuntu", series="24.04"),
        ),
    ]


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "architecture-agnostic",
                "build-base": "ubuntu@20.04",
                "platforms": {
                    "all": {
                        "build_on": ["amd64", "arm64"],
                        "build_for": "all",
                    },
                },
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_architecture_agnostic(build_plan_service: BuildPlanService):
    assert build_plan(build_plan_service, ["amd64"]) == [
        BuildInfo(
            platform="all",
            build_on=DebianArchitecture.AMD64,
            build_for="all",
            build_base=DistroBase(distribution="ubuntu", series="20.04"),
        ),
    ]

    assert build_plan(build_plan_service, ["arm64"]) == [
        BuildInfo(
            platform="all",
            build_on=DebianArchitecture.ARM64,
            build_for="all",
            build_base=DistroBase(distribution="ubuntu", series="20.04"),
        ),
    ]


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "multi-base-architecture-agnostic",
                "platforms": {
                    "noble": {
                        "build_on": ["ubuntu@24.04:amd64", "ubuntu@24.04:arm64"],
                        "build_for": "ubuntu@24.04:all",
                    },
                    "jammy": {
                        "build_on": ["ubuntu@22.04:amd64", "ubuntu@22.04:arm64"],
                        "build_for": "ubuntu@22.04:all",
                    },
                },
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_multi_base_architecture_agnostic(build_plan_service: BuildPlanService):
    assert build_plan(build_plan_service, ["amd64"]) == [
        BuildInfo(
            platform="noble",
            build_on=DebianArchitecture.AMD64,
            build_for="all",
            build_base=DistroBase(distribution="ubuntu", series="24.04"),
        ),
        BuildInfo(
            platform="jammy",
            build_on=DebianArchitecture.AMD64,
            build_for="all",
            build_base=DistroBase(distribution="ubuntu", series="22.04"),
        ),
    ]

    assert build_plan(build_plan_service, ["arm64"]) == [
        BuildInfo(
            platform="noble",
            build_on=DebianArchitecture.ARM64,
            build_for="all",
            build_base=DistroBase(distribution="ubuntu", series="24.04"),
        ),
        BuildInfo(
            platform="jammy",
            build_on=DebianArchitecture.ARM64,
            build_for="all",
            build_base=DistroBase(distribution="ubuntu", series="22.04"),
        ),
    ]


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "multi-base-i386-s390x",
                "platforms": {
                    "x86": {
                        "build_on": ["ubuntu@24.04:i386", "ubuntu@24.04:amd64"],
                        "build_for": "ubuntu@24.04:i386",
                    },
                    "arm": {
                        "build_on": ["ubuntu@24.04:armhf", "ubuntu@24.04:arm64"],
                        "build_for": ["ubuntu@24.04:armhf"],
                    },
                    "legacy": {
                        "build_on": "ubuntu@20.04:i386",
                        "build_for": "ubuntu@20.04:i386",
                    },
                },
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_multi_base_extended(build_plan_service: BuildPlanService):
    assert build_plan(build_plan_service, ["amd64", "arm64"]) == [
        BuildInfo(
            platform="x86",
            build_on=DebianArchitecture.AMD64,
            build_for=DebianArchitecture.I386,
            build_base=DistroBase(distribution="ubuntu", series="24.04"),
        ),
        BuildInfo(
            platform="arm",
            build_on=DebianArchitecture.ARM64,
            build_for=DebianArchitecture.ARMHF,
            build_base=DistroBase(distribution="ubuntu", series="24.04"),
        ),
    ]

    assert build_plan(build_plan_service, ["i386", "armhf"]) == [
        BuildInfo(
            platform="x86",
            build_on=DebianArchitecture.I386,
            build_for=DebianArchitecture.I386,
            build_base=DistroBase(distribution="ubuntu", series="24.04"),
        ),
        BuildInfo(
            platform="arm",
            build_on=DebianArchitecture.ARMHF,
            build_for=DebianArchitecture.ARMHF,
            build_base=DistroBase(distribution="ubuntu", series="24.04"),
        ),
        BuildInfo(
            platform="legacy",
            build_on=DebianArchitecture.I386,
            build_for=DebianArchitecture.I386,
            build_base=DistroBase(distribution="ubuntu", series="20.04"),
        ),
    ]


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "multi-base-override-base",
                "base": "ubuntu@24.04",
                "platforms": {"ubuntu@20.04:i386": None, "s390x": None},
            },
            id="override_base",
        ),
        pytest.param(
            {
                "name": "multi-base-build-on-mismatch",
                "platforms": {
                    "ppc64el": {
                        "build-on": ["ubuntu@22.04:ppc64el", "ubuntu@24.04:ppc64el"],
                        "build-for": ["ubuntu@24.04:ppc64el"],
                    },
                },
            },
            id="build_on_mismatch",
        ),
        pytest.param(
            {
                "name": "multi-base-no-build-on-base",
                "platforms": {
                    "ppc64el": {
                        "build-on": ["ppc64el"],
                        "build-for": ["ubuntu@22.04:ppc64el"],
                    },
                },
            },
            id="no_build_on_base",
        ),
        pytest.param(
            {
                "name": "multi-base-no-build-for-base",
                "platforms": {
                    "ppc64el": {
                        "build-on": ["ubuntu@22.04:ppc64el"],
                        "build-for": ["ppc64el"],
                    },
                },
            },
            id="no_build_for_base",
        ),
    ],
)
def test_multi_base_errors(build_plan_service: BuildPlanService):
    with pytest.raises(InvalidMultiBaseError):
        build_plan(build_plan_service)


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "repeated-platform-shorthand",
                "base": "ubuntu@24.04",
                "platforms": {
                    "amd64": None,
                    "x64": {
                        "build-on": "amd64",
                        "build-for": "amd64",
                    },
                },
            },
            id="shorthand",
        ),
        pytest.param(
            {
                "name": "repeated-platform-expanded",
                "base": "ubuntu@24.04",
                "platforms": {
                    "native": {
                        "build-on": ["amd64", "i386"],
                        "build-for": ["i386"],
                    },
                    "emulated": {
                        "build-on": "arm64",
                        "build-for": "i386",
                    },
                },
            },
            id="expanded",
        ),
        pytest.param(
            {
                "name": "repeated-platform-multi-base",
                "platforms": {
                    "noble": {
                        "build-on": ["ubuntu@24.04:ppc64el"],
                        "build-for": ["ubuntu@24.04:ppc64el"],
                    },
                    "jammy": {
                        "build-on": ["ubuntu@22.04:ppc64el"],
                        "build-for": ["ubuntu@22.04:ppc64el"],
                    },
                    "focal": {
                        "build-on": ["ubuntu@20.04:ppc64el"],
                        "build-for": ["ubuntu@20.04:ppc64el"],
                    },
                    "typo": {
                        "build-on": ["ubuntu@24.04:ppc64el"],
                        "build-for": ["ubuntu@24.04:ppc64el"],
                    },
                },
            },
            id="multi_base",
        ),
    ],
)
def test_repeated_platform_errors(build_plan_service: BuildPlanService):
    with pytest.raises(RepeatedPlatformError):
        build_plan(build_plan_service)


@pytest.mark.parametrize(
    "project_data",
    [
        pytest.param(
            {
                "name": "repeated-platform-shorthand",
                "base": "ubuntu@24.04",
                "platforms": {
                    "all": {
                        "build_on": ["amd64", "arm64"],
                        "build_for": "all",
                    },
                    "ppc64el": None,
                },
            },
            id=pytest.HIDDEN_PARAM,
        ),
    ],
)
def test_all_only_build_errors(build_plan_service: BuildPlanService):
    with pytest.raises(AllOnlyBuildError):
        build_plan(build_plan_service)


def build_plan(
    build_plan_service: BuildPlanService, build_on: list[str] | None = None
) -> list[BuildInfo]:
    return list(
        build_plan_service.create_build_plan(
            platforms=None, build_for=None, build_on=build_on
        )
    )
