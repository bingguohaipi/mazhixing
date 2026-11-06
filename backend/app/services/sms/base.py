"""SMS provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class SmsPurpose(str, Enum):
    REGISTER = "register"
    RESET_PASSWORD = "reset_password"


@dataclass(frozen=True)
class SmsSendResult:
    """Result of sending a verification code (optional fields per provider)."""

    out_id: str | None = None
    dev_code: str | None = None


class SmsProvider(ABC):
    @property
    def uses_remote_verification(self) -> bool:
        """If True, verification is done via provider API (e.g. Dypns CheckSmsVerifyCode)."""
        return False

    @abstractmethod
    def send_verification_code(
        self,
        phone: str,
        code: str,
        purpose: SmsPurpose,
        *,
        out_id: str | None = None,
    ) -> SmsSendResult:
        """Send verification code; raise AppException on failure."""

    def check_verification_code(self, phone: str, code: str, out_id: str | None) -> None:
        """Verify code with provider when uses_remote_verification is True."""
        raise NotImplementedError
