"""Aliyun phone number verification (Dypnsapi) — SendSmsVerifyCode / CheckSmsVerifyCode."""

from __future__ import annotations

import logging
from uuid import uuid4

from alibabacloud_dypnsapi20170525 import models as dypns_models
from alibabacloud_dypnsapi20170525.client import Client as DypnsClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

from app.core.exceptions import AppException
from app.services.sms.base import SmsProvider, SmsPurpose, SmsSendResult

logger = logging.getLogger(__name__)

DYPNS_PLACEHOLDER_CODE = "__dypns__"

_RAM_PERMISSION_HINT = (
    "当前 AccessKey 所属 RAM 用户没有号码认证短信权限。"
    "请在 RAM 控制台为该用户授权 AliyunDypnsFullAccess，"
    "或自定义策略包含 dypns:SendSmsVerifyCode、dypns:CheckSmsVerifyCode。"
)


def _map_dypns_client_error(exc: Exception) -> AppException:
    code = getattr(exc, "code", None) or ""
    if code == "Forbidden.NoPermission":
        return AppException(403, _RAM_PERMISSION_HINT, status_code=403)
    return AppException(500, "短信发送失败，请稍后重试", status_code=500)


class AliyunDypnsSmsProvider(SmsProvider):
    """验证码由阿里云生成并发送，核验走 CheckSmsVerifyCode。"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        sign_name: str,
        template_code: str,
        template_param: str,
        *,
        scheme_name: str | None = None,
        country_code: str = "86",
        valid_time_seconds: int = 300,
        send_interval_seconds: int = 60,
        code_length: int = 6,
        return_verify_code_in_debug: bool = False,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.sign_name = sign_name
        self.template_code = template_code
        self.template_param = template_param
        self.scheme_name = scheme_name
        self.country_code = country_code
        self.valid_time_seconds = valid_time_seconds
        self.send_interval_seconds = send_interval_seconds
        self.code_length = code_length
        self.return_verify_code_in_debug = return_verify_code_in_debug
        self.timeout_seconds = timeout_seconds
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        self._client = self._create_client(access_key_id, access_key_secret)

    def _ensure_credentials(self) -> None:
        for label, value in (
            ("AccessKey ID", self._access_key_id),
            ("AccessKey Secret", self._access_key_secret),
        ):
            if not value or "在这里" in value or not value.isascii():
                raise AppException(
                    500,
                    f"{label} 未正确配置：请在 backend/.env.local 填入 RAM 中的英文 AccessKey，保存后重启后端",
                    status_code=500,
                )

    @property
    def uses_remote_verification(self) -> bool:
        return True

    @staticmethod
    def _create_client(access_key_id: str, access_key_secret: str) -> DypnsClient:
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        config.endpoint = "dypnsapi.aliyuncs.com"
        config.read_timeout = int(8000)
        config.connect_timeout = int(5000)
        return DypnsClient(config)

    def send_verification_code(
        self,
        phone: str,
        code: str,
        purpose: SmsPurpose,
        *,
        out_id: str | None = None,
    ) -> SmsSendResult:
        del code, purpose
        self._ensure_credentials()
        external_id = out_id or uuid4().hex
        request = dypns_models.SendSmsVerifyCodeRequest(
            phone_number=phone,
            sign_name=self.sign_name,
            template_code=self.template_code,
            template_param=self.template_param,
            country_code=self.country_code,
            out_id=external_id,
            interval=self.send_interval_seconds,
            valid_time=self.valid_time_seconds,
            code_length=self.code_length,
            code_type=1,
            duplicate_policy=1,
            return_verify_code=self.return_verify_code_in_debug,
        )
        if self.scheme_name:
            request.scheme_name = self.scheme_name

        runtime = util_models.RuntimeOptions()
        runtime.read_timeout = int(self.timeout_seconds * 1000)

        try:
            response = self._client.send_sms_verify_code_with_options(request, runtime)
        except Exception as exc:
            logger.error("Dypns SendSmsVerifyCode error: %s", getattr(exc, "code", exc))
            raise _map_dypns_client_error(exc) from exc

        body = response.body
        if body is None or body.code != "OK":
            message = body.message if body else "未知错误"
            logger.error("Dypns send rejected: code=%s message=%s", getattr(body, "code", None), message)
            raise AppException(500, "短信发送失败，请稍后重试", status_code=500)

        model = body.model
        resolved_out_id = external_id
        dev_code: str | None = None
        if model is not None:
            if model.out_id:
                resolved_out_id = model.out_id
            if model.verify_code:
                dev_code = model.verify_code

        return SmsSendResult(out_id=resolved_out_id, dev_code=dev_code)

    def check_verification_code(self, phone: str, code: str, out_id: str | None) -> None:
        request = dypns_models.CheckSmsVerifyCodeRequest(
            phone_number=phone,
            verify_code=code,
            country_code=self.country_code,
            out_id=out_id,
            case_auth_policy=1,
        )
        if self.scheme_name:
            request.scheme_name = self.scheme_name

        runtime = util_models.RuntimeOptions()
        runtime.read_timeout = int(self.timeout_seconds * 1000)

        try:
            response = self._client.check_sms_verify_code_with_options(request, runtime)
        except Exception as exc:
            logger.error("Dypns CheckSmsVerifyCode error: %s", getattr(exc, "code", exc))
            mapped = _map_dypns_client_error(exc)
            if mapped.status_code == 403:
                raise mapped
            raise AppException(400, "验证码无效或已过期") from exc

        body = response.body
        if body is None or body.code != "OK":
            raise AppException(400, "验证码无效或已过期")

        verify_result = body.model.verify_result if body.model else None
        if verify_result != "PASS":
            raise AppException(400, "验证码无效或已过期")
