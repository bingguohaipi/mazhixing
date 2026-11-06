import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.audit import OperationLog
from app.models.user import User, UserRole
from app.models.verification_code import VerificationCode, VerificationPurpose
from app.utils.user_info import build_user_info
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
    UserInfo,
)
from app.services.sms import get_sms_provider
from app.services.sms.base import SmsPurpose
from app.services.sms.dypns_provider import DYPNS_PLACEHOLDER_CODE


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def _log(self, user_id: int | None, action: str, detail: str | None = None, ip: str | None = None) -> None:
        self.db.add(
            OperationLog(
                user_id=user_id,
                action=action,
                resource="auth",
                detail=detail,
                ip_address=ip,
            )
        )

    def send_verification_code(
        self,
        phone: str,
        purpose: VerificationPurpose,
        role: UserRole | None = None,
    ) -> str:
        if purpose == VerificationPurpose.REGISTER:
            if role is None:
                raise AppException(400, "注册需指定角色")
            existing = self._get_user_by_account(phone, role)
            if existing:
                raise AppException(400, "该手机号已注册")

        if purpose == VerificationPurpose.RESET_PASSWORD:
            if role is None:
                raise AppException(400, "重置密码需指定角色")
            existing = self._get_user_by_account(phone, role)
            if not existing:
                raise AppException(404, "该手机号未注册")

        provider = get_sms_provider()
        use_dypns = self.settings.sms_enabled and provider.uses_remote_verification

        if use_dypns:
            out_id = uuid4().hex
            valid_seconds = self.settings.aliyun_dypns_valid_time_seconds
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=valid_seconds)
            stored_code = DYPNS_PLACEHOLDER_CODE
        else:
            out_id = None
            stored_code = (
                self.settings.dev_sms_code
                if self.settings.debug
                else f"{random.randint(100000, 999999):06d}"
            )
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        dev_return_code = stored_code

        if self.settings.sms_enabled:
            sms_purpose = (
                SmsPurpose.REGISTER
                if purpose == VerificationPurpose.REGISTER
                else SmsPurpose.RESET_PASSWORD
            )
            send_result = provider.send_verification_code(
                phone,
                stored_code if not use_dypns else "",
                sms_purpose,
                out_id=out_id,
            )
            if use_dypns:
                out_id = send_result.out_id or out_id
                if send_result.dev_code:
                    dev_return_code = send_result.dev_code

        self.db.add(
            VerificationCode(
                phone=phone,
                code=stored_code,
                out_id=out_id,
                purpose=purpose,
                role=role.value if role else None,
                expires_at=expires_at,
            )
        )
        self.db.commit()

        return dev_return_code

    def verify_code(self, phone: str, code: str, purpose: VerificationPurpose, role: UserRole | None = None) -> None:
        now = datetime.now(timezone.utc)
        provider = get_sms_provider()
        use_dypns = self.settings.sms_enabled and provider.uses_remote_verification

        query = (
            self.db.query(VerificationCode)
            .filter(
                VerificationCode.phone == phone,
                VerificationCode.purpose == purpose,
                VerificationCode.is_used.is_(False),
                VerificationCode.expires_at >= now,
            )
            .order_by(VerificationCode.id.desc())
        )
        if role:
            query = query.filter(VerificationCode.role == role.value)

        if use_dypns:
            record = query.filter(VerificationCode.out_id.isnot(None)).first()
            if record is None:
                raise AppException(400, "验证码无效或已过期")
            provider.check_verification_code(phone, code, record.out_id)
            record.is_used = True
            return

        query = query.filter(VerificationCode.code == code)
        record = query.first()
        if record is None:
            raise AppException(400, "验证码无效或已过期")

        record.is_used = True

    def register(self, payload: RegisterRequest, ip: str | None = None) -> UserInfo:
        role = UserRole(payload.role)
        self.verify_code(payload.phone, payload.code, VerificationPurpose.REGISTER, role)

        user = User(
            account=payload.phone,
            phone=payload.phone,
            password_hash=hash_password(payload.password),
            role=role,
            display_name=payload.display_name or self._default_display_name(role),
        )
        self.db.add(user)
        self._log(None, "register", f"role={role.value}, phone={payload.phone}", ip)
        self.db.commit()
        self.db.refresh(user)
        return build_user_info(user, self.db)

    def login(self, payload: LoginRequest, ip: str | None = None) -> LoginResponse:
        role = UserRole(payload.role)
        user = self._get_user_by_account(payload.account, role)
        if user is None:
            self._log(None, "login_failed", f"account={payload.account}, role={role.value}", ip)
            self.db.commit()
            mismatch = self._role_mismatch_message(payload.account, payload.password, role)
            raise AppException(401, mismatch or "账号或密码错误", status_code=401)

        if not verify_password(payload.password, user.password_hash):
            self._log(user.id, "login_failed", "invalid_password", ip)
            self.db.commit()
            raise AppException(401, "账号或密码错误", status_code=401)

        user.token_version += 1
        tokens = self._issue_tokens(user)
        self._log(user.id, "login_success", None, ip)
        self.db.commit()
        return LoginResponse(tokens=tokens, user=build_user_info(user, self.db))

    def refresh(self, refresh_token: str) -> TokenPair:
        from app.core.security import safe_decode_token

        payload = safe_decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise AppException(401, "无效的刷新令牌", status_code=401)

        user = self.db.get(User, int(payload["sub"]))
        if user is None or user.deleted_at is not None or not user.is_active:
            raise AppException(401, "用户不存在或已被禁用", status_code=401)

        if payload.get("role") != user.role.value:
            raise AppException(401, "角色信息不匹配", status_code=401)

        token_version = payload.get("tv")
        if token_version is not None and int(token_version) != user.token_version:
            raise AppException(401, "账号已在其他设备登录，请重新登录", status_code=401)

        return self._issue_tokens(user)

    def change_password(self, user: User, payload: ChangePasswordRequest, ip: str | None = None) -> None:
        if not verify_password(payload.old_password, user.password_hash):
            raise AppException(400, "原密码错误")

        if verify_password(payload.new_password, user.password_hash):
            raise AppException(400, "新密码不能与原密码相同")

        user.password_hash = hash_password(payload.new_password)
        user.token_version += 1
        self._log(user.id, "change_password", None, ip)
        self.db.commit()

    def reset_password(self, payload: ResetPasswordRequest, ip: str | None = None) -> None:
        role = UserRole(payload.role)
        self.verify_code(payload.phone, payload.code, VerificationPurpose.RESET_PASSWORD, role)

        user = self._get_user_by_account(payload.phone, role)
        if user is None:
            raise AppException(404, "用户不存在")

        user.password_hash = hash_password(payload.new_password)
        user.token_version += 1
        self._log(user.id, "reset_password", None, ip)
        self.db.commit()

    def _get_user_by_account(self, account: str, role: UserRole) -> User | None:
        return (
            self.db.query(User)
            .filter(
                User.account == account,
                User.role == role,
                User.deleted_at.is_(None),
            )
            .first()
        )

    def _find_users_by_account(self, account: str) -> list[User]:
        return (
            self.db.query(User)
            .filter(User.account == account, User.deleted_at.is_(None), User.is_active.is_(True))
            .all()
        )

    @staticmethod
    def _role_display(role: UserRole) -> str:
        mapping = {
            UserRole.TEACHER: "教师",
            UserRole.STUDENT: "学生",
            UserRole.PARENT: "家长",
            UserRole.ADMIN: "管理员",
        }
        return mapping.get(role, role.value)

    def _role_mismatch_message(self, account: str, password: str, selected_role: UserRole) -> str | None:
        """密码正确但所选登录身份与账号角色不一致时，引导用户返回选择身份。"""
        for user in self._find_users_by_account(account):
            if user.role == selected_role:
                continue
            if verify_password(password, user.password_hash):
                actual = self._role_display(user.role)
                return f"该账号已注册为{actual}身份，请点击「返回选择身份」后选择「{actual}」再登录"
        return None

    def _issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(user.id, user.role.value, user.token_version),
            refresh_token=create_refresh_token(user.id, user.role.value, user.token_version),
        )

    @staticmethod
    def _default_display_name(role: UserRole) -> str:
        mapping = {
            UserRole.TEACHER: "教师用户",
            UserRole.PARENT: "家长用户",
            UserRole.STUDENT: "学生用户",
        }
        return mapping[role]
