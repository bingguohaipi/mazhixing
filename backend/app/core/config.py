from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET_KEYS = {
    "dev-secret-key-change-in-production",
    "change-me-to-a-random-secret-key-in-production",
    "replace-with-a-long-random-secret",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # `.env.local` 覆盖 `.env`，便于本机 uvicorn 与 Docker 生产配置共存
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "码智星 OJ 平台"
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    database_url: str = "sqlite:///./mazhixing.db"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    dev_sms_code: str = "123456"
    sms_enabled: bool = True
    sms_provider: str = "mock"
    sms_timeout_seconds: float = 8.0
    aliyun_sms_access_key_id: str | None = None
    aliyun_sms_access_key_secret: str | None = None
    aliyun_sms_sign_name: str | None = None
    aliyun_sms_template_code: str | None = None
    aliyun_sms_template_code_register: str | None = None
    aliyun_sms_template_code_reset: str | None = None
    aliyun_dypns_access_key_id: str | None = None
    aliyun_dypns_access_key_secret: str | None = None
    aliyun_dypns_sign_name: str | None = None
    aliyun_dypns_template_code: str | None = None
    aliyun_dypns_template_param: str = '{"code":"##code##","min":"5"}'
    aliyun_dypns_scheme_name: str | None = None
    aliyun_dypns_country_code: str = "86"
    aliyun_dypns_valid_time_seconds: int = 300
    aliyun_dypns_send_interval_seconds: int = 60
    aliyun_dypns_code_length: int = 6
    metrics_enabled: bool = True
    metrics_token: str | None = None
    enable_seed: bool | None = None
    enable_openapi: bool | None = None
    rate_limit_enabled: bool = True
    operation_log_retention_days: int = 90
    event_log_retention_days: int = 30

    # 判题
    judge0_url: str | None = None
    judge0_auth_token: str | None = None
    judge0_required: bool = False
    judge0_allow_local_fallback: bool = True
    judge0_health_timeout_seconds: float = 5.0
    judge_async: bool = True
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = True

    # AI 解析
    ai_enabled: bool = True
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    ai_daily_limit: int = 5
    ai_teacher_daily_limit: int = 10
    ai_timeout_seconds: int = 8

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def use_async_judge(self) -> bool:
        return self.judge_async and not self.celery_task_always_eager

    @property
    def is_production(self) -> bool:
        return not self.debug

    @property
    def should_seed(self) -> bool:
        if self.enable_seed is not None:
            return self.enable_seed
        return self.debug

    @property
    def should_expose_openapi(self) -> bool:
        if self.enable_openapi is not None:
            return self.enable_openapi
        return self.debug

    def validate_judge_config(self) -> None:
        if self.judge0_required and not self.judge0_url:
            raise RuntimeError("JUDGE0_REQUIRED=true 时必须设置 JUDGE0_URL")
        if self.is_production and not self.judge0_url:
            import warnings

            warnings.warn(
                "生产环境未配置 JUDGE0_URL，代码将在宿主机 subprocess 中执行，存在安全风险",
                stacklevel=2,
            )

    def validate_production(self) -> None:
        if self.debug:
            return

        if self.secret_key in _INSECURE_SECRET_KEYS or len(self.secret_key) < 32:
            raise RuntimeError("生产环境必须设置长度不少于 32 的随机 SECRET_KEY")

        if self.database_url.startswith("sqlite"):
            raise RuntimeError("生产环境禁止使用 SQLite，请配置 MySQL DATABASE_URL")

        if not self.judge0_url:
            raise RuntimeError("生产环境必须配置 JUDGE0_URL")

        if self.judge0_allow_local_fallback:
            raise RuntimeError("生产环境必须设置 JUDGE0_ALLOW_LOCAL_FALLBACK=false")

        if self.celery_task_always_eager:
            raise RuntimeError("生产环境必须设置 CELERY_TASK_ALWAYS_EAGER=false")

        if not self.cors_origin_list or "localhost" in self.cors_origins:
            import warnings

            warnings.warn("生产环境 CORS_ORIGINS 应配置为正式域名", stacklevel=2)

        if self.ai_enabled and not self.openai_api_key:
            raise RuntimeError("生产环境 AI_ENABLED=true 时必须配置 OPENAI_API_KEY")

        if self.sms_enabled and self.sms_provider == "aliyun":
            missing = [
                name
                for name, value in [
                    ("ALIYUN_SMS_ACCESS_KEY_ID", self.aliyun_sms_access_key_id),
                    ("ALIYUN_SMS_ACCESS_KEY_SECRET", self.aliyun_sms_access_key_secret),
                    ("ALIYUN_SMS_SIGN_NAME", self.aliyun_sms_sign_name),
                    ("ALIYUN_SMS_TEMPLATE_CODE", self.aliyun_sms_template_code),
                ]
                if not value
            ]
            if missing:
                raise RuntimeError(f"生产环境短信服务缺少配置: {', '.join(missing)}")

        if self.sms_enabled and self.sms_provider in ("dypns", "aliyun_dypns"):
            ak = self.aliyun_dypns_access_key_id or self.aliyun_sms_access_key_id
            sk = self.aliyun_dypns_access_key_secret or self.aliyun_sms_access_key_secret
            missing = [
                name
                for name, value in [
                    ("ALIYUN_DYPNS_ACCESS_KEY_ID / ALIYUN_SMS_ACCESS_KEY_ID", ak),
                    ("ALIYUN_DYPNS_ACCESS_KEY_SECRET / ALIYUN_SMS_ACCESS_KEY_SECRET", sk),
                    ("ALIYUN_DYPNS_SIGN_NAME", self.aliyun_dypns_sign_name),
                    ("ALIYUN_DYPNS_TEMPLATE_CODE", self.aliyun_dypns_template_code),
                ]
                if not value
            ]
            if missing:
                raise RuntimeError(f"生产环境号码认证短信缺少配置: {', '.join(missing)}")

        self.validate_judge_config()


@lru_cache
def get_settings() -> Settings:
    return Settings()
