import pytest

from app.core.code_validation import validate_submission_code
from app.core.exceptions import AppException


def test_reject_empty_code() -> None:
    with pytest.raises(AppException) as exc:
        validate_submission_code("   ", "Python")
    assert exc.value.message == "请勿提交空代码"


def test_reject_too_short_code() -> None:
    with pytest.raises(AppException) as exc:
        validate_submission_code("# only\n", "Python")
    assert "过少" in exc.value.message


def test_reject_dangerous_python() -> None:
    code = "import os\nos.system('ls')\nprint('hello world test')"
    with pytest.raises(AppException) as exc:
        validate_submission_code(code, "Python")
    assert "不允许" in exc.value.message


def test_accept_valid_python() -> None:
    code = "a = input()\nprint(int(a) + 1)\n"
    validate_submission_code(code, "Python")
