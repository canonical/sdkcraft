from __future__ import annotations

import pytest
from sdkcraft.errors import ShellCheckError
from sdkcraft.linters.shellcheck import ShellCheck

pytestmark = [pytest.mark.slow]


def test_shellcheck_no_files(tmp_path_factory: pytest.TempPathFactory):
    path = tmp_path_factory.mktemp("sdk")
    (path / "hooks").mkdir()

    issues = ShellCheck().run(path)
    assert issues == []


def test_shellcheck_error(tmp_path_factory: pytest.TempPathFactory):
    path = tmp_path_factory.mktemp("sdk")
    hook = path / "hooks" / "setup-base"

    hook.parent.mkdir()
    hook.write_text("")
    hook.chmod(0)

    with pytest.raises(ShellCheckError):
        ShellCheck().run(path)


def test_shellcheck_external_sources(tmp_path_factory: pytest.TempPathFactory):
    path = tmp_path_factory.mktemp("sdk")
    hook = path / "hooks" / "setup-project"
    helper = hook.with_name("utils.sh")

    hook.parent.mkdir()
    hook.write_text("""\
# shellcheck source=hooks/utils.sh
. $SDK/sdk/hooks/utils.sh
""")
    helper.write_text("""\
touch '~/.profile'
""")

    issues = ShellCheck().run(path)
    assert len(issues) == 2
    issues.sort(key=lambda issue: issue.path)

    expected = issues[0].model_copy(
        update={
            "linter": "shellcheck",
            "path": hook.relative_to(path),
            "abspath": hook,
            "line": 2,
            "end_line": 2,
            "column": 3,
            "end_column": 6,
        }
    )
    assert issues[0] == expected

    expected = issues[1].model_copy(
        update={
            "linter": "shellcheck",
            "path": helper.relative_to(path),
            "abspath": helper,
            "line": 1,
            "end_line": 1,
            "column": 7,
            "end_column": 18,
        }
    )
    assert issues[1] == expected
