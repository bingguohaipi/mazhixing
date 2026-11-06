"""Aliyun SMS ( dysmsapi ) provider."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import urllib.parse
from base64 import b64encode
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from app.core.exceptions import AppException
from app.services.sms.base import SmsProvider, SmsPurpose, SmsSendResult

logger = logging.getLogger(__name__)

ALIYUN_SMS_ENDPOINT = "https://dysmsapi.aliyuncs.com/"


class AliyunSmsProvider(SmsProvider):
    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        sign_name: str,
        template_code: str,
        template_code_register: str | None = None,
        template_code_reset: str | None = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.template_code = template_code
        self.template_code_register = template_code_register or template_code
        self.template_code_reset = template_code_reset or template_code
        self.timeout_seconds = timeout_seconds

    def send_verification_code(
        self,
        phone: str,
        code: str,
        purpose: SmsPurpose,
        *,
        out_id: str | None = None,
    ) -> SmsSendResult:
        template = (
            self.template_code_register
            if purpose == SmsPurpose.REGISTER
            else self.template_code_reset
        )
        params = {
            "Action": "SendSms",
            "Version": "2017-05-25",
            "RegionId": "cn-hangzhou",
            "PhoneNumbers": phone,
            "SignName": self.sign_name,
            "TemplateCode": template,
            "TemplateParam": json.dumps({"code": code}, ensure_ascii=False),
            "Format": "JSON",
            "AccessKeyId": self.access_key_id,
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "SignatureVersion": "1.0",
            "SignatureNonce": uuid4().hex,
        }
        params["Signature"] = self._sign(params)

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(ALIYUN_SMS_ENDPOINT, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            logger.exception("Aliyun SMS HTTP error: %s", exc)
            raise AppException(500, "短信发送失败，请稍后重试", status_code=500) from exc

        if payload.get("Code") != "OK":
            message = payload.get("Message", "未知错误")
            logger.error("Aliyun SMS rejected: Code=%s Message=%s", payload.get("Code"), message)
            raise AppException(500, "短信发送失败，请稍后重试", status_code=500)

        return SmsSendResult()

    def _sign(self, params: dict[str, str]) -> str:
        sorted_params = sorted(params.items())
        query = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)
        string_to_sign = f"GET&{urllib.parse.quote('/', safe='')}&{urllib.parse.quote(query, safe='')}"
        digest = hmac.new(
            f"{self.access_key_secret}&".encode(),
            string_to_sign.encode(),
            hashlib.sha1,
        ).digest()
        return b64encode(digest).decode()
