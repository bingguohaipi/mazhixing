"""Development SMS provider — logs only, never sends."""

import logging

from app.services.sms.base import SmsProvider, SmsPurpose, SmsSendResult

logger = logging.getLogger(__name__)


class MockSmsProvider(SmsProvider):
    def send_verification_code(
        self,
        phone: str,
        code: str,
        purpose: SmsPurpose,
        *,
        out_id: str | None = None,
    ) -> SmsSendResult:
        logger.info("SMS mock: phone=%s purpose=%s code=%s", phone, purpose.value, code)
        return SmsSendResult()
