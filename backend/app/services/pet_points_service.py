from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.pet import (
    PetSystemConfig,
    PointFirstAcGrant,
    PointLedger,
    PointLedgerType,
    StudentPointsAccount,
)
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.schemas.pet_points_schema import PointLedgerItem, PointLedgerListResponse, StudentPointsSummary


class PetPointsService:
    MAX_POINTS_PER_FIRST_AC = 10

    def __init__(self, db: Session):
        self.db = db

    def _ensure_config(self) -> PetSystemConfig:
        config = self.db.query(PetSystemConfig).filter(PetSystemConfig.id == 1).first()
        if config is None:
            config = PetSystemConfig(
                id=1,
                points_launched_at=datetime.now(timezone.utc),
                points_per_first_ac=self.MAX_POINTS_PER_FIRST_AC,
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        elif config.points_launched_at is None:
            config.points_launched_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(config)
        return config

    def _ensure_account(self, student_id: int) -> StudentPointsAccount:
        account = self.db.get(StudentPointsAccount, student_id)
        if account is None:
            account = StudentPointsAccount(student_id=student_id)
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
        return account

    def get_summary(self, student_id: int) -> StudentPointsSummary:
        account = self._ensure_account(student_id)
        first_ac_count = (
            self.db.query(func.count(PointFirstAcGrant.id))
            .filter(PointFirstAcGrant.student_id == student_id)
            .scalar()
            or 0
        )
        return StudentPointsSummary(
            balance=account.balance,
            total_earned=account.total_earned,
            total_spent=account.total_spent,
            first_ac_count=int(first_ac_count),
        )

    def list_ledger(
        self,
        student_id: int,
        ledger_type: str | None,
        page: int,
        page_size: int,
    ) -> PointLedgerListResponse:
        query = self.db.query(PointLedger).filter(PointLedger.student_id == student_id)
        if ledger_type:
            query = query.filter(PointLedger.type == PointLedgerType(ledger_type))
        total = query.count()
        rows = (
            query.order_by(PointLedger.created_at.desc(), PointLedger.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = [
            PointLedgerItem(
                id=row.id,
                type=row.type.value,
                delta=row.delta,
                balance_after=row.balance_after,
                ref_type=row.ref_type,  # type: ignore[arg-type]
                ref_id=row.ref_id,
                ref_title=row.ref_title,
                created_at=row.created_at,
            )
            for row in rows
        ]
        return PointLedgerListResponse(items=items, total=total, page=page, page_size=page_size)

    def try_grant_first_ac(self, submission: Submission) -> None:
        if submission.status != SubmissionStatus.AC:
            return

        from app.models.user import User, UserRole

        user = self.db.get(User, submission.user_id)
        if user is None or user.role != UserRole.STUDENT:
            return

        config = self._ensure_config()
        judged_at = submission.updated_at or submission.created_at
        if judged_at.tzinfo is None:
            judged_at = judged_at.replace(tzinfo=timezone.utc)
        launched = config.points_launched_at
        if launched is not None and launched.tzinfo is None:
            launched = launched.replace(tzinfo=timezone.utc)
        if launched is not None and judged_at < launched:
            return

        existing = (
            self.db.query(PointFirstAcGrant)
            .filter(
                PointFirstAcGrant.student_id == submission.user_id,
                PointFirstAcGrant.problem_id == submission.problem_id,
            )
            .first()
        )
        if existing is not None:
            return

        points = config.points_per_first_ac
        account = self._ensure_account(submission.user_id)
        account.balance += points
        account.total_earned += points

        problem = self.db.get(Problem, submission.problem_id)
        title = problem.title if problem else None

        self.db.add(
            PointFirstAcGrant(
                student_id=submission.user_id,
                problem_id=submission.problem_id,
                submission_id=submission.id,
            )
        )
        self.db.add(
            PointLedger(
                student_id=submission.user_id,
                type=PointLedgerType.EARN_FIRST_AC,
                delta=points,
                balance_after=account.balance,
                ref_type="problem",
                ref_id=submission.problem_id,
                ref_title=title,
            )
        )
        self.db.commit()

    def submission_points_fields(self, submission_id: int) -> tuple[int | None, int | None]:
        grant = (
            self.db.query(PointFirstAcGrant)
            .filter(PointFirstAcGrant.submission_id == submission_id)
            .first()
        )
        if grant is None:
            return None, None
        config = self._ensure_config()
        account = self._ensure_account(grant.student_id)
        return config.points_per_first_ac, account.balance

    def spend_points(
        self,
        student_id: int,
        amount: int,
        ref_title: str,
        ref_id: int | None = None,
    ) -> int:
        if amount <= 0:
            raise AppException(400, "无效扣款金额")
        account = self._ensure_account(student_id)
        if account.balance < amount:
            raise AppException(400, "积分不足")
        account.balance -= amount
        account.total_spent += amount
        self.db.add(
            PointLedger(
                student_id=student_id,
                type=PointLedgerType.SPEND_SHOP,
                delta=-amount,
                balance_after=account.balance,
                ref_type="shop_order",
                ref_id=ref_id,
                ref_title=ref_title,
            )
        )
        self.db.flush()
        return account.balance
