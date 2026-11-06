"""Arena (擂台) business logic."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.arena import (
    ArenaResult,
    ArenaReviewStatus,
    ArenaSession,
    ArenaSessionMetrics,
    ArenaSessionStatus,
    UserNotification,
)
from app.models.problem import Problem, ProblemDifficulty, ProblemLanguage
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.schemas.arena_schema import (
    ArenaBoardEntry,
    ArenaBoardResponse,
    ArenaGlobalLeaderboardEntry,
    ArenaGlobalLeaderboardResponse,
    ArenaOverviewResponse,
    ArenaProblemListItem,
    ArenaProblemListResponse,
    ArenaResultBrief,
    ArenaSessionBrief,
    ArenaSessionDetail,
    ArenaSessionMetricsPatch,
    ArenaNotificationItem,
    ArenaNotificationListResponse,
)
from app.schemas.submission_schema import SubmissionDetail
from app.services.problem_access import ProblemAccessHelper
from app.services.submission_service import SubmissionService

SESSION_TTL_MINUTES = 30
BASELINE_MS = 60_000
GLOBAL_ACCURACY_WEIGHT = 0.70
GLOBAL_TIME_WEIGHT = 0.30
# 全站总榜综合分：通过题数占 40%，其余 60% 按正确率 70% + 相对耗时 30% 分配（即 42% + 18%）
GLOBAL_PASSED_WEIGHT = 0.40


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
PASTE_RATIO_THRESHOLD = 0.65
FAST_SUBMIT_SECONDS = 12
SIMILARITY_PENDING_THRESHOLD = 0.88
AUTO_APPROVE_SIMILARITY = 0.92


class ArenaService:
    def __init__(self, db: Session):
        self.db = db

    def agree_terms(self, user_id: int) -> None:
        user = self._get_student(user_id)
        user.arena_agreed_at = datetime.now(timezone.utc)
        self.db.commit()

    def create_session(self, user_id: int, problem_id: int, language: str) -> ArenaSessionDetail:
        user = self._get_student(user_id)
        if user.arena_agreed_at is None:
            raise AppException(403, "请先阅读并同意擂台规则", status_code=403)

        problem = self._get_arena_problem(user_id, problem_id)
        from app.utils.problem_languages import problem_supports_language

        if not problem_supports_language(problem, language):
            raise AppException(400, "该题不支持所选编程语言")

        self._expire_stale_sessions(user_id)
        active = self._active_session(user_id, problem_id, language)
        if active is not None:
            raise AppException(409, "该题已有进行中的擂台")

        now = datetime.now(timezone.utc)
        session = ArenaSession(
            user_id=user_id,
            problem_id=problem_id,
            language=language,
            status=ArenaSessionStatus.IN_PROGRESS,
            started_at=now,
            expires_at=now + timedelta(minutes=SESSION_TTL_MINUTES),
        )
        self.db.add(session)
        self.db.flush()
        self.db.add(ArenaSessionMetrics(arena_session_id=session.id))
        self.db.commit()
        self.db.refresh(session)
        return self._to_session_detail(session)

    def exit_session(self, user_id: int, session_id: int) -> None:
        session = self._get_owned_session(user_id, session_id)
        if session.status != ArenaSessionStatus.IN_PROGRESS:
            raise AppException(400, "当前状态不可退出")
        session.status = ArenaSessionStatus.EXITED
        session.exited_at = datetime.now(timezone.utc)
        self.db.commit()

    def patch_metrics(self, user_id: int, session_id: int, payload: ArenaSessionMetricsPatch) -> None:
        session = self._get_owned_session(user_id, session_id)
        if session.status != ArenaSessionStatus.IN_PROGRESS:
            return
        metrics = self.db.get(ArenaSessionMetrics, session_id)
        if metrics is None:
            metrics = ArenaSessionMetrics(arena_session_id=session_id)
            self.db.add(metrics)
        metrics.paste_count = payload.paste_count
        metrics.paste_char_count = payload.paste_char_count
        metrics.first_keystroke_at = payload.first_keystroke_at
        self.db.commit()

    def submit_session(self, user_id: int, session_id: int, code: str) -> tuple[SubmissionDetail, ArenaResultBrief | None]:
        session = self._get_owned_session(user_id, session_id)
        self._ensure_session_active(session)
        if session.submission_id is not None:
            raise AppException(400, "请勿重复提交，本次擂台已结束")

        detail = SubmissionService(self.db).create_arena_submission(
            user_id=user_id,
            arena_session_id=session.id,
            problem_id=session.problem_id,
            code=code,
            language=session.language,
        )
        now = datetime.now(timezone.utc)
        session.status = ArenaSessionStatus.SUBMITTED
        session.submitted_at = now
        session.submission_id = detail.id
        self.db.commit()

        result = (
            self.db.query(ArenaResult)
            .filter(ArenaResult.arena_session_id == session.id)
            .first()
        )
        brief = self._to_result_brief(result) if result else None
        refreshed = SubmissionService(self.db).get_submission(detail.id, user_id)
        return refreshed, brief

    def get_session(self, user_id: int, session_id: int) -> ArenaSessionDetail:
        session = self._get_owned_session(user_id, session_id)
        self._maybe_expire(session)
        return self._to_session_detail(session)

    def get_overview(self, user_id: int) -> ArenaOverviewResponse:
        self._get_student(user_id)
        self._expire_stale_sessions(user_id)
        active = (
            self.db.query(ArenaSession)
            .filter(
                ArenaSession.user_id == user_id,
                ArenaSession.status == ArenaSessionStatus.IN_PROGRESS,
            )
            .order_by(ArenaSession.id.desc())
            .first()
        )
        unread = (
            self.db.query(func.count(UserNotification.id))
            .filter(UserNotification.user_id == user_id, UserNotification.is_read.is_(False))
            .scalar()
            or 0
        )
        hot: list[ArenaProblemListItem] = []
        if active is not None:
            hot = self.list_arena_problems(
                user_id,
                page=1,
                page_size=5,
                language=active.language,
            ).items
        return ArenaOverviewResponse(
            active_session=self._to_session_brief(active) if active else None,
            unread_notifications=unread,
            hot_problems=hot,
        )

    def list_arena_problems(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        difficulty: str | None = None,
        language: str | None = None,
    ) -> ArenaProblemListResponse:
        """与公共题库列表同一数据源与筛选、排序规则；language 可选，不传则返回全部公共题。"""
        from app.utils.problem_languages import apply_language_filter

        query = ProblemAccessHelper(self.db).list_public_catalog_query()
        if language is not None:
            if language not in ("Python", "C++"):
                raise AppException(400, "language 须为 Python 或 C++")
            query = apply_language_filter(query, language)
        if keyword:
            like = f"%{keyword.strip()}%"
            if keyword.strip().isdigit():
                query = query.filter((Problem.title.ilike(like)) | (Problem.id == int(keyword.strip())))
            else:
                query = query.filter(Problem.title.ilike(like))
        if difficulty:
            query = query.filter(Problem.difficulty == ProblemDifficulty(difficulty))

        total = query.count()
        problems = (
            query.order_by(Problem.public_group_id.desc(), Problem.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = [self._to_problem_item(p, user_id) for p in problems]
        return ArenaProblemListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_board(self, user_id: int, problem_id: int, language: str, limit: int = 20) -> ArenaBoardResponse:
        self._get_student(user_id)
        problem = self._get_arena_problem(user_id, problem_id)
        from app.utils.problem_languages import problem_supports_language

        if not problem_supports_language(problem, language):
            raise AppException(400, "该题不支持所选编程语言")

        entries = self._build_board_entries(problem_id, language, user_id, limit)
        my_status, my_entry = self._resolve_my_board_status(user_id, problem_id, language, entries)
        participants = self._participant_count(problem_id, language)
        return ArenaBoardResponse(
            problem_id=problem_id,
            language=language,
            entries=entries,
            my_entry=my_entry,
            my_status=my_status,
            total_participants=participants,
        )

    @staticmethod
    def _global_composite_score(
        problems_passed: int,
        max_passed: int,
        accuracy: float,
        relative_time: float,
    ) -> float:
        passed_ratio = problems_passed / max_passed if max_passed else 0.0
        quality_scale = 1.0 - GLOBAL_PASSED_WEIGHT
        quality_acc = accuracy * GLOBAL_ACCURACY_WEIGHT
        quality_time = (1.0 - relative_time) * GLOBAL_TIME_WEIGHT
        return round(
            passed_ratio * GLOBAL_PASSED_WEIGHT * 100
            + quality_acc * quality_scale * 100
            + quality_time * quality_scale * 100,
            2,
        )

    def get_global_leaderboard(
        self, viewer_id: int, language: str, limit: int = 50
    ) -> ArenaGlobalLeaderboardResponse:
        self._get_student(viewer_id)
        if language not in ("Python", "C++"):
            raise AppException(400, "language 须为 Python 或 C++")

        @dataclass
        class _Agg:
            user: User
            attempt_count: int = 0
            ac_count: int = 0
            problems_passed: set[int] = field(default_factory=set)
            total_duration_ms: int = 0

        rows = (
            self.db.query(ArenaResult, User)
            .join(User, User.id == ArenaResult.user_id)
            .filter(
                ArenaResult.language == language,
                User.deleted_at.is_(None),
                User.arena_ranking_opt_out.is_(False),
            )
            .all()
        )

        agg_by_user: dict[int, _Agg] = {}
        for result, user in rows:
            bucket = agg_by_user.get(user.id)
            if bucket is None:
                bucket = _Agg(user=user)
                agg_by_user[user.id] = bucket
            bucket.attempt_count += 1
            bucket.total_duration_ms += result.duration_ms
            if result.judge_status == SubmissionStatus.AC:
                bucket.ac_count += 1
                if result.review_status == ArenaReviewStatus.APPROVED:
                    bucket.problems_passed.add(result.problem_id)

        if not agg_by_user:
            return ArenaGlobalLeaderboardResponse(
                language=language,
                entries=[],
                my_entry=None,
                total_participants=0,
            )

        max_duration = max(item.total_duration_ms for item in agg_by_user.values()) or 1
        max_passed = max(len(item.problems_passed) for item in agg_by_user.values()) or 1
        scored: list[tuple[_Agg, float, float]] = []
        for item in agg_by_user.values():
            accuracy = item.ac_count / item.attempt_count if item.attempt_count else 0.0
            relative_time = item.total_duration_ms / max_duration
            composite = self._global_composite_score(
                len(item.problems_passed),
                max_passed,
                accuracy,
                relative_time,
            )
            scored.append((item, accuracy, composite))

        # 通过题数优先；仅当通过题数相同时，综合分（含通过题数权重）才参与排序
        scored.sort(
            key=lambda row: (
                -len(row[0].problems_passed),
                -row[2],
                row[0].total_duration_ms,
            )
        )

        display_rows = scored[:limit]
        suffix_map = self._duplicate_suffix_map([row[0].user for row in display_rows])

        entries: list[ArenaGlobalLeaderboardEntry] = []
        my_entry: ArenaGlobalLeaderboardEntry | None = None
        for index, (item, accuracy, composite) in enumerate(display_rows, start=1):
            entry = ArenaGlobalLeaderboardEntry(
                rank=index,
                user_id=item.user.id,
                display_name=self._display_name(item.user),
                student_no_suffix=suffix_map.get(item.user.id),
                problems_passed=len(item.problems_passed),
                attempt_count=item.attempt_count,
                ac_count=item.ac_count,
                accuracy_rate=round(accuracy * 100, 1),
                total_duration_ms=item.total_duration_ms,
                composite_score=round(composite, 2),
                is_me=item.user.id == viewer_id,
            )
            entries.append(entry)
            if item.user.id == viewer_id:
                my_entry = entry

        if my_entry is None:
            for index, (item, accuracy, composite) in enumerate(scored, start=1):
                if item.user.id != viewer_id:
                    continue
                my_entry = ArenaGlobalLeaderboardEntry(
                    rank=index,
                    user_id=item.user.id,
                    display_name=self._display_name(item.user),
                    student_no_suffix=None,
                    problems_passed=len(item.problems_passed),
                    attempt_count=item.attempt_count,
                    ac_count=item.ac_count,
                    accuracy_rate=round(accuracy * 100, 1),
                    total_duration_ms=item.total_duration_ms,
                    composite_score=round(composite, 2),
                    is_me=True,
                )
                break

        return ArenaGlobalLeaderboardResponse(
            language=language,
            entries=entries,
            my_entry=my_entry,
            total_participants=len(agg_by_user),
        )

    def list_notifications(
        self, user_id: int, page: int = 1, page_size: int = 20
    ) -> ArenaNotificationListResponse:
        query = self.db.query(UserNotification).filter(UserNotification.user_id == user_id)
        total = query.count()
        rows = query.order_by(UserNotification.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        items = [
            ArenaNotificationItem(
                id=row.id,
                event_key=row.event_key,
                title=row.title,
                body=row.body,
                is_read=row.is_read,
                created_at=row.created_at,
                payload_json=row.payload_json,
            )
            for row in rows
        ]
        return ArenaNotificationListResponse(items=items, total=total, page=page, page_size=page_size)

    def mark_notifications_read(self, user_id: int, ids: list[int] | None, mark_all: bool) -> int:
        query = self.db.query(UserNotification).filter(UserNotification.user_id == user_id, UserNotification.is_read.is_(False))
        if not mark_all:
            if not ids:
                return 0
            query = query.filter(UserNotification.id.in_(ids))
        now = datetime.now(timezone.utc)
        count = 0
        for row in query.all():
            row.is_read = True
            row.read_at = now
            count += 1
        self.db.commit()
        return count

    def process_after_judge(self, submission_id: int) -> None:
        submission = self.db.get(Submission, submission_id)
        if submission is None or submission.arena_session_id is None:
            return
        if submission.status == SubmissionStatus.PENDING:
            return

        session = self.db.get(ArenaSession, submission.arena_session_id)
        if session is None:
            return

        existing = (
            self.db.query(ArenaResult)
            .filter(ArenaResult.arena_session_id == session.id)
            .first()
        )
        if existing is not None:
            return

        submitted_at = session.submitted_at or submission.created_at
        judged_at = submission.updated_at or datetime.now(timezone.utc)
        duration_ms = max(int((judged_at - submitted_at).total_seconds() * 1000), 0)

        review_status = ArenaReviewStatus.NONE
        arena_score: float | None = None
        ranked_at = None
        achieved_at = judged_at if submission.status == SubmissionStatus.AC else None

        old_ranks: dict[int, int] = {}
        if submission.status == SubmissionStatus.AC:
            arena_score = self._compute_score(duration_ms, submission.problem_id)
            review_status = self._decide_review(submission, session, duration_ms)
            if review_status == ArenaReviewStatus.APPROVED:
                ranked_at = datetime.now(timezone.utc)
                old_ranks = self._rank_map(submission.problem_id, submission.language)

        result = ArenaResult(
            arena_session_id=session.id,
            user_id=submission.user_id,
            problem_id=submission.problem_id,
            language=submission.language,
            submission_id=submission.id,
            judge_status=submission.status,
            duration_ms=duration_ms,
            arena_score=arena_score,
            review_status=review_status,
            ranked_at=ranked_at,
            achieved_at=achieved_at,
        )
        self.db.add(result)
        self.db.commit()

        self._notify_post_result(submission, result)
        if review_status == ArenaReviewStatus.APPROVED:
            self._notify_rank_changes(
                submission.problem_id,
                submission.language,
                submission.user_id,
                old_ranks=old_ranks,
            )

    def admin_set_arena_enabled(self, problem_id: int, enabled: bool) -> None:
        problem = self.db.get(Problem, problem_id)
        if problem is None or problem.deleted_at is not None:
            raise AppException(404, "题目不存在")
        was_enabled = problem.arena_enabled
        problem.arena_enabled = enabled
        if enabled and not was_enabled and problem.arena_opened_at is None:
            problem.arena_opened_at = datetime.now(timezone.utc)
        self.db.commit()
        if enabled and not was_enabled:
            self._broadcast_problem_open(problem)

    # --- internals ---

    def _get_student(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if user is None or user.role != UserRole.STUDENT or user.deleted_at is not None:
            raise AppException(403, "仅学生可参与擂台")
        return user

    def _get_arena_problem(self, user_id: int, problem_id: int) -> Problem:
        problem = self.db.get(Problem, problem_id)
        if problem is None or problem.deleted_at is not None:
            raise AppException(404, "题目不存在")
        helper = ProblemAccessHelper(self.db)
        if not helper.is_public_catalog_problem(problem):
            raise AppException(403, "仅公共题库已上架题目可打擂台")
        if not helper.student_can_access_problem(user_id, problem):
            raise AppException(403, "暂无权限挑战该题")
        return problem

    def _get_owned_session(self, user_id: int, session_id: int) -> ArenaSession:
        session = self.db.get(ArenaSession, session_id)
        if session is None or session.user_id != user_id:
            raise AppException(404, "擂台会话不存在或已结束")
        return session

    def _active_session(self, user_id: int, problem_id: int, language: str) -> ArenaSession | None:
        return (
            self.db.query(ArenaSession)
            .filter(
                ArenaSession.user_id == user_id,
                ArenaSession.problem_id == problem_id,
                ArenaSession.language == language,
                ArenaSession.status == ArenaSessionStatus.IN_PROGRESS,
            )
            .first()
        )

    def _maybe_expire(self, session: ArenaSession) -> None:
        if session.status != ArenaSessionStatus.IN_PROGRESS:
            return
        if datetime.now(timezone.utc) > _as_utc(session.expires_at):
            session.status = ArenaSessionStatus.EXPIRED
            self.db.commit()

    def _ensure_session_active(self, session: ArenaSession) -> None:
        self._maybe_expire(session)
        if session.status != ArenaSessionStatus.IN_PROGRESS:
            raise AppException(410, "擂台已超时，请重新打擂台")

    def _expire_stale_sessions(self, user_id: int) -> None:
        now = datetime.now(timezone.utc)
        rows = (
            self.db.query(ArenaSession)
            .filter(
                ArenaSession.user_id == user_id,
                ArenaSession.status == ArenaSessionStatus.IN_PROGRESS,
                ArenaSession.expires_at.isnot(None),
            )
            .all()
        )
        changed = False
        for row in rows:
            if _as_utc(row.expires_at) < now:
                row.status = ArenaSessionStatus.EXPIRED
                changed = True
        if changed:
            self.db.commit()

    def _compute_score(self, duration_ms: int, problem_id: int) -> float:
        baseline = self._baseline_ms(problem_id)
        speed = max(0.0, min(100.0, 100.0 * (1.0 - duration_ms / baseline)))
        stability = 100.0
        return round(speed * 0.6 + stability * 0.4, 2)

    def _baseline_ms(self, problem_id: int) -> float:
        median = (
            self.db.query(func.avg(ArenaResult.duration_ms))
            .filter(
                ArenaResult.problem_id == problem_id,
                ArenaResult.review_status == ArenaReviewStatus.APPROVED,
                ArenaResult.judge_status == SubmissionStatus.AC,
            )
            .scalar()
        )
        if median and median > 0:
            return max(float(median), float(BASELINE_MS))
        return float(BASELINE_MS)

    def _decide_review(self, submission: Submission, session: ArenaSession, duration_ms: int) -> ArenaReviewStatus:
        user = self.db.get(User, submission.user_id)
        if user and user.arena_ranking_opt_out:
            return ArenaReviewStatus.APPROVED

        metrics = self.db.get(ArenaSessionMetrics, session.id)
        flags: list[str] = []
        risk = 0.0
        code_len = max(len(submission.code.strip()), 1)
        paste_ratio = (metrics.paste_char_count / code_len) if metrics else 0.0
        if metrics and metrics.paste_count > 0 and paste_ratio >= PASTE_RATIO_THRESHOLD:
            if duration_ms < FAST_SUBMIT_SECONDS * 1000:
                flags.append("fast_paste")
                risk += 0.5

        similarity = self._max_similarity(submission)
        if metrics:
            metrics.similarity_max = similarity
            metrics.risk_score = risk + similarity * 0.5
            metrics.risk_flags = json.dumps(flags) if flags else None

        if similarity >= SIMILARITY_PENDING_THRESHOLD and similarity < AUTO_APPROVE_SIMILARITY:
            flags.append("high_similarity")
        if flags:
            if metrics:
                metrics.risk_flags = json.dumps(flags)
                metrics.risk_score = min(1.0, metrics.risk_score + 0.3)
            # 无管理端人工审核时仍写入风险指标，成绩直接上榜
        return ArenaReviewStatus.APPROVED

    def _max_similarity(self, submission: Submission) -> float:
        normalized = self._normalize_code(submission.code)
        others = (
            self.db.query(Submission.code)
            .filter(
                Submission.problem_id == submission.problem_id,
                Submission.id != submission.id,
                Submission.status == SubmissionStatus.AC,
            )
            .limit(50)
            .all()
        )
        best = 0.0
        for (code,) in others:
            ratio = SequenceMatcher(None, normalized, self._normalize_code(code)).ratio()
            best = max(best, ratio)
        return best

    @staticmethod
    def _normalize_code(code: str) -> str:
        text = re.sub(r"\s+", " ", code.strip())
        return text.lower()

    def _best_results_query(self, problem_id: int, language: str):
        return (
            self.db.query(ArenaResult)
            .join(User, User.id == ArenaResult.user_id)
            .filter(
                ArenaResult.problem_id == problem_id,
                ArenaResult.language == language,
                ArenaResult.review_status == ArenaReviewStatus.APPROVED,
                ArenaResult.judge_status == SubmissionStatus.AC,
                User.arena_ranking_opt_out.is_(False),
                User.deleted_at.is_(None),
            )
        )

    def _build_board_entries(
        self, problem_id: int, language: str, viewer_id: int, limit: int
    ) -> list[ArenaBoardEntry]:
        rows = self._best_results_query(problem_id, language).all()
        best_by_user: dict[int, ArenaResult] = {}
        for row in rows:
            current = best_by_user.get(row.user_id)
            if current is None or self._is_better(row, current):
                best_by_user[row.user_id] = row

        sorted_rows = sorted(
            best_by_user.values(),
            key=lambda r: (-(r.arena_score or 0), r.duration_ms, r.achieved_at or r.created_at),
        )[:limit]

        users = {
            u.id: u
            for u in self.db.query(User).filter(User.id.in_([r.user_id for r in sorted_rows])).all()
        }
        suffix_map = self._duplicate_suffix_map([users[r.user_id] for r in sorted_rows if r.user_id in users])

        entries: list[ArenaBoardEntry] = []
        for index, row in enumerate(sorted_rows, start=1):
            user = users.get(row.user_id)
            if user is None:
                continue
            entries.append(
                ArenaBoardEntry(
                    rank=index,
                    user_id=row.user_id,
                    display_name=self._display_name(user),
                    student_no_suffix=suffix_map.get(row.user_id),
                    arena_score=row.arena_score or 0.0,
                    duration_ms=row.duration_ms,
                    achieved_at=row.achieved_at or row.created_at,
                    is_me=row.user_id == viewer_id,
                )
            )
        return entries

    def _rank_map(self, problem_id: int, language: str) -> dict[int, int]:
        entries = self._build_board_entries(problem_id, language, viewer_id=0, limit=10_000)
        return {entry.user_id: entry.rank for entry in entries}

    def _is_better(self, candidate: ArenaResult, current: ArenaResult) -> bool:
        c_score = candidate.arena_score or 0
        cur_score = current.arena_score or 0
        if c_score != cur_score:
            return c_score > cur_score
        if candidate.duration_ms != current.duration_ms:
            return candidate.duration_ms < current.duration_ms
        c_time = candidate.achieved_at or candidate.created_at
        cur_time = current.achieved_at or current.created_at
        return c_time < cur_time

    def _participant_count(self, problem_id: int, language: str) -> int:
        return (
            self.db.query(func.count(func.distinct(ArenaResult.user_id)))
            .filter(
                ArenaResult.problem_id == problem_id,
                ArenaResult.language == language,
                ArenaResult.review_status == ArenaReviewStatus.APPROVED,
            )
            .scalar()
            or 0
        )

    def _resolve_my_board_status(
        self,
        user_id: int,
        problem_id: int,
        language: str,
        entries: list[ArenaBoardEntry],
    ) -> tuple[str, ArenaBoardEntry | None]:
        active = self._active_session(user_id, problem_id, language)
        if active is not None:
            return "in_progress", None

        pending = (
            self.db.query(ArenaResult)
            .filter(
                ArenaResult.user_id == user_id,
                ArenaResult.problem_id == problem_id,
                ArenaResult.language == language,
                ArenaResult.review_status == ArenaReviewStatus.PENDING,
            )
            .first()
        )
        if pending is not None:
            return "pending_review", None

        rejected = (
            self.db.query(ArenaResult)
            .filter(
                ArenaResult.user_id == user_id,
                ArenaResult.problem_id == problem_id,
                ArenaResult.language == language,
                ArenaResult.review_status == ArenaReviewStatus.REJECTED,
            )
            .order_by(ArenaResult.id.desc())
            .first()
        )
        if rejected is not None and not any(e.is_me for e in entries):
            return "rejected", None

        my_entry = next((e for e in entries if e.is_me), None)
        if my_entry:
            return "on_board", my_entry
        return "none", None

    def _to_problem_item(self, problem: Problem, user_id: int) -> ArenaProblemListItem:
        from app.utils.problem_languages import get_problem_languages

        langs = get_problem_languages(problem)
        lang = langs[0]
        board = self._build_board_entries(problem.id, lang, user_id, limit=1)
        champion = board[0] if board else None
        return ArenaProblemListItem(
            id=problem.id,
            title=problem.title,
            language=lang,
            languages=langs,
            difficulty=problem.difficulty.value,
            gesp_level=problem.gesp_level.value,
            knowledge_point=problem.knowledge_point,
            champion_name=champion.display_name if champion else None,
            champion_score=champion.arena_score if champion else None,
            participant_count=self._participant_count(problem.id, lang),
        )

    def _notify_post_result(self, submission: Submission, result: ArenaResult) -> None:
        problem = self.db.get(Problem, submission.problem_id)
        title = problem.title if problem else f"#{submission.problem_id}"
        if submission.status == SubmissionStatus.AC:
            if result.review_status == ArenaReviewStatus.APPROVED:
                self._push_notification(
                    submission.user_id,
                    "arena_ac_personal_best",
                    "擂台 AC",
                    f"你在《{title}》{submission.language} 擂台 AC，成绩已计入榜单。",
                    {"problem_id": submission.problem_id, "language": submission.language},
                )
            return
        status_label = submission.status.value
        self._push_notification(
            submission.user_id,
            "arena_not_ac",
            "本次未 AC",
            f"《{title}》{submission.language} 擂台未通过（{status_label}），可重新打擂台。",
            {"problem_id": submission.problem_id, "language": submission.language},
        )

    def _notify_rank_changes(
        self,
        problem_id: int,
        language: str,
        actor_user_id: int,
        old_ranks: dict[int, int] | None = None,
    ) -> None:
        if old_ranks is None:
            old_ranks = {}
        new_entries = self._build_board_entries(problem_id, language, actor_user_id, limit=10_000)
        new_ranks = {e.user_id: e.rank for e in new_entries}
        actor = self.db.get(User, actor_user_id)
        actor_name = self._display_name(actor) if actor else "某同学"
        problem = self.db.get(Problem, problem_id)
        title = problem.title if problem else f"#{problem_id}"

        actor_rank = new_ranks.get(actor_user_id)
        if actor_rank == 1:
            self._push_notification(
                actor_user_id,
                "arena_take_first",
                "夺擂成功",
                f"恭喜！你已成为《{title}》{language} 全站榜主。",
                {"problem_id": problem_id, "language": language},
            )

        for user_id, old_rank in old_ranks.items():
            if user_id == actor_user_id:
                continue
            new_rank = new_ranks.get(user_id)
            if new_rank is None:
                continue
            if new_rank > old_rank:
                user = self.db.get(User, user_id)
                if user and user.arena_ranking_opt_out:
                    continue
                self._push_notification(
                    user_id,
                    "arena_overtaken",
                    "排名变动",
                    f"{actor_name} 在《{title}》{language} 擂台超过你，你现为第 {new_rank} 名。",
                    {"problem_id": problem_id, "language": language, "rank": new_rank},
                )

    def _broadcast_problem_open(self, problem: Problem) -> None:
        students = (
            self.db.query(User)
            .filter(User.role == UserRole.STUDENT, User.deleted_at.is_(None), User.is_active.is_(True))
            .all()
        )
        for student in students:
            self._push_notification(
                student.id,
                "arena_problem_open",
                "新擂台开放",
                f"《{problem.title}》已开放 {problem.language.value} 擂台，快来挑战。",
                {"problem_id": problem.id, "language": problem.language.value},
            )

    def _push_notification(
        self,
        user_id: int,
        event_key: str,
        title: str,
        body: str,
        payload: dict,
    ) -> None:
        self.db.add(
            UserNotification(
                user_id=user_id,
                event_key=event_key,
                title=title,
                body=body,
                payload_json=json.dumps(payload, ensure_ascii=False),
            )
        )
        self.db.commit()

    @staticmethod
    def _display_name(user: User) -> str:
        return user.display_name or user.account

    def _duplicate_suffix_map(self, users: list[User]) -> dict[int, str | None]:
        name_counts: dict[str, int] = {}
        for user in users:
            name = self._display_name(user)
            name_counts[name] = name_counts.get(name, 0) + 1
        suffix: dict[int, str | None] = {}
        for user in users:
            name = self._display_name(user)
            if name_counts.get(name, 0) > 1 and user.student_no:
                suffix[user.id] = user.student_no[-4:]
            else:
                suffix[user.id] = None
        return suffix

    @staticmethod
    def _to_session_brief(session: ArenaSession) -> ArenaSessionBrief:
        return ArenaSessionBrief(
            id=session.id,
            problem_id=session.problem_id,
            language=session.language,
            status=session.status.value,
            started_at=session.started_at,
            expires_at=session.expires_at,
            submitted_at=session.submitted_at,
        )

    def _to_session_detail(self, session: ArenaSession) -> ArenaSessionDetail:
        brief = self._to_session_brief(session)
        return ArenaSessionDetail(**brief.model_dump(), submission_id=session.submission_id)

    @staticmethod
    def _to_result_brief(result: ArenaResult | None) -> ArenaResultBrief | None:
        if result is None:
            return None
        return ArenaResultBrief(
            review_status=result.review_status.value,
            arena_score=result.arena_score,
            duration_ms=result.duration_ms,
            judge_status=result.judge_status.value,
        )
