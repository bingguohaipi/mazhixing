from functools import lru_cache

from app.core.config import get_settings
from app.services.sms.aliyun_provider import AliyunSmsProvider
from app.services.sms.base import SmsProvider
from app.services.sms.dypns_provider import AliyunDypnsSmsProvider
from app.services.sms.mock_provider import MockSmsProvider


@lru_cache
def get_sms_provider() -> SmsProvider:
    settings = get_settings()
    provider = settings.sms_provider.lower()

    if provider == "mock" or not settings.sms_enabled:
        return MockSmsProvider()

    if provider == "aliyun":
        return AliyunSmsProvider(
            access_key_id=settings.aliyun_sms_access_key_id or "",
            access_key_secret=settings.aliyun_sms_access_key_secret or "",
            sign_name=settings.aliyun_sms_sign_name or "",
            template_code=settings.aliyun_sms_template_code or "",
            template_code_register=settings.aliyun_sms_template_code_register,
            template_code_reset=settings.aliyun_sms_template_code_reset,
            timeout_seconds=settings.sms_timeout_seconds,
        )

    if provider in ("dypns", "aliyun_dypns"):
        return AliyunDypnsSmsProvider(
            access_key_id=settings.aliyun_dypns_access_key_id
            or settings.aliyun_sms_access_key_id
            or "",
            access_key_secret=settings.aliyun_dypns_access_key_secret
            or settings.aliyun_sms_access_key_secret
            or "",
            sign_name=settings.aliyun_dypns_sign_name or "",
            template_code=settings.aliyun_dypns_template_code or "",
            template_param=settings.aliyun_dypns_template_param,
            scheme_name=settings.aliyun_dypns_scheme_name,
            country_code=settings.aliyun_dypns_country_code,
            valid_time_seconds=settings.aliyun_dypns_valid_time_seconds,
            send_interval_seconds=settings.aliyun_dypns_send_interval_seconds,
            code_length=settings.aliyun_dypns_code_length,
            return_verify_code_in_debug=settings.debug,
            timeout_seconds=settings.sms_timeout_seconds,
        )

    raise RuntimeError(f"不支持的 SMS_PROVIDER: {provider}")
