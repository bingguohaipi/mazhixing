"""Dypns SMS provider integration with auth service (mocked API)."""

from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.user import UserRole
from app.models.verification_code import VerificationCode, VerificationPurpose
from app.services.auth_service import AuthService
from app.services.sms.base import SmsSendResult


def _settings_mock(*, sms_enabled: bool = True) -> MagicMock:
    settings = MagicMock()
    settings.sms_enabled = sms_enabled
    settings.debug = True
    settings.dev_sms_code = "123456"
    settings.aliyun_dypns_valid_time_seconds = 300
    return settings


def test_dypns_send_and_verify(db: Session) -> None:
    provider = MagicMock()
    provider.uses_remote_verification = True
    provider.send_verification_code.return_value = SmsSendResult(out_id="out-123", dev_code="654321")
    provider.check_verification_code.return_value = None

    with patch("app.services.auth_service.get_sms_provider", return_value=provider):
        with patch("app.services.auth_service.get_settings", return_value=_settings_mock()):
            service = AuthService(db)
            code = service.send_verification_code(
                "13800001111",
                VerificationPurpose.REGISTER,
                role=UserRole.TEACHER,
            )

    assert code == "654321"
    row = db.query(VerificationCode).filter(VerificationCode.phone == "13800001111").one()
    assert row.out_id == "out-123"

    with patch("app.services.auth_service.get_sms_provider", return_value=provider):
        with patch("app.services.auth_service.get_settings", return_value=_settings_mock()):
            service = AuthService(db)
            service.verify_code(
                "13800001111",
                "654321",
                VerificationPurpose.REGISTER,
                role=UserRole.TEACHER,
            )

    provider.check_verification_code.assert_called_once_with("13800001111", "654321", "out-123")
    db.flush()
    assert (
        db.query(VerificationCode)
        .filter(VerificationCode.phone == "13800001111")
        .one()
        .is_used
        is True
    )
