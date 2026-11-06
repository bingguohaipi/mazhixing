from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.audit import OperationLog, ParentStudentBinding
from app.models.class_model import ClassEnrollment, TeachingClass
from app.models.notice import Notice, NoticeClass, NoticeRead
from app.models.user import User, UserRole
from app.schemas.notice_schema import NoticeCreateRequest, NoticeFeedItem, NoticeListItem


class NoticeService:
    def __init__(self, db: Session):
        self.db = db

    def _log(self, user_id: int, action: str, detail: str | None = None) -> None:
        self.db.add(OperationLog(user_id=user_id, action=action, resource="notice", detail=detail))

    def create_notice(self, teacher_id: int, payload: NoticeCreateRequest) -> NoticeListItem:
        class_ids = list(dict.fromkeys(payload.class_ids))
        self._validate_classes(teacher_id, class_ids)

        notice = Notice(
            teacher_id=teacher_id,
            title=payload.title.strip(),
            content=payload.content.strip(),
            created_by=teacher_id,
            updated_by=teacher_id,
        )
        self.db.add(notice)
        self.db.flush()

        for class_id in class_ids:
            self.db.add(NoticeClass(notice_id=notice.id, class_id=class_id))

        self._log(teacher_id, "create_notice", f"notice_id={notice.id}, classes={class_ids}")
        self.db.commit()
        self.db.refresh(notice)
        return self._to_list_item(notice)

    def list_teacher_notices(self, teacher_id: int) -> list[NoticeListItem]:
        notices = (
            self.db.query(Notice)
            .filter(Notice.teacher_id == teacher_id, Notice.deleted_at.is_(None))
            .order_by(Notice.id.desc())
            .all()
        )
        return [self._to_list_item(item) for item in notices]

    def list_feed_for_student(self, student_id: int) -> list[NoticeFeedItem]:
        class_ids = self._student_class_ids(student_id)
        return self._list_feed_by_class_ids(class_ids, student_id)

    def list_feed_for_parent(self, parent_id: int) -> list[NoticeFeedItem]:
        student_ids = [
            row.student_id
            for row in self.db.query(ParentStudentBinding.student_id)
            .filter(ParentStudentBinding.parent_id == parent_id)
            .all()
        ]
        class_ids: set[int] = set()
        for student_id in student_ids:
            class_ids.update(self._student_class_ids(student_id))
        return self._list_feed_by_class_ids(list(class_ids), parent_id)

    def mark_notice_read(self, user_id: int, notice_id: int) -> None:
        class_ids = self._feed_class_ids_for_user(user_id)
        if not class_ids:
            raise AppException(403, "暂无权限访问该通知")
        allowed_ids = self._notice_ids_for_classes(class_ids)
        if notice_id not in allowed_ids:
            raise AppException(404, "通知不存在")

        existing = (
            self.db.query(NoticeRead)
            .filter(NoticeRead.notice_id == notice_id, NoticeRead.user_id == user_id)
            .first()
        )
        if existing is None:
            self.db.add(NoticeRead(notice_id=notice_id, user_id=user_id))
            self.db.commit()
        else:
            self.db.commit()

    def delete_notice(self, notice_id: int, teacher_id: int) -> None:
        notice = self._get_owned_notice(notice_id, teacher_id)
        notice.deleted_at = datetime.now(timezone.utc)
        notice.updated_by = teacher_id
        self._log(teacher_id, "delete_notice", f"notice_id={notice_id}")
        self.db.commit()

    def _validate_classes(self, teacher_id: int, class_ids: list[int]) -> None:
        owned = {
            row.id
            for row in self.db.query(TeachingClass.id)
            .filter(
                TeachingClass.id.in_(class_ids),
                TeachingClass.teacher_id == teacher_id,
                TeachingClass.deleted_at.is_(None),
            )
            .all()
        }
        missing = [class_id for class_id in class_ids if class_id not in owned]
        if missing:
            raise AppException(400, "包含无效或无权限的班级")

    def _get_owned_notice(self, notice_id: int, teacher_id: int) -> Notice:
        notice = (
            self.db.query(Notice)
            .filter(
                Notice.id == notice_id,
                Notice.teacher_id == teacher_id,
                Notice.deleted_at.is_(None),
            )
            .first()
        )
        if notice is None:
            self._log(teacher_id, "access_denied", f"notice_id={notice_id}")
            self.db.commit()
            raise AppException(404, "通知不存在")
        return notice

    def _student_class_ids(self, student_id: int) -> list[int]:
        return [
            row.class_id
            for row in self.db.query(ClassEnrollment.class_id)
            .filter(ClassEnrollment.student_id == student_id, ClassEnrollment.deleted_at.is_(None))
            .all()
        ]

    def _feed_class_ids_for_user(self, user_id: int) -> list[int]:
        user = self.db.get(User, user_id)
        if user is None or user.deleted_at is not None:
            return []
        if user.role == UserRole.STUDENT:
            return self._student_class_ids(user_id)
        if user.role == UserRole.PARENT:
            student_ids = [
                row.student_id
                for row in self.db.query(ParentStudentBinding.student_id)
                .filter(ParentStudentBinding.parent_id == user_id)
                .all()
            ]
            class_ids: set[int] = set()
            for student_id in student_ids:
                class_ids.update(self._student_class_ids(student_id))
            return list(class_ids)
        return []

    def _notice_ids_for_classes(self, class_ids: list[int]) -> set[int]:
        if not class_ids:
            return set()
        rows = (
            self.db.query(NoticeClass.notice_id)
            .filter(NoticeClass.class_id.in_(class_ids))
            .distinct()
            .all()
        )
        return {row.notice_id for row in rows}

    def _list_feed_by_class_ids(self, class_ids: list[int], viewer_user_id: int) -> list[NoticeFeedItem]:
        if not class_ids:
            return []

        notice_ids = list(self._notice_ids_for_classes(class_ids))
        if not notice_ids:
            return []

        notices = (
            self.db.query(Notice)
            .filter(Notice.id.in_(notice_ids), Notice.deleted_at.is_(None))
            .order_by(Notice.id.desc())
            .limit(50)
            .all()
        )

        read_ids = {
            row.notice_id
            for row in self.db.query(NoticeRead.notice_id)
            .filter(NoticeRead.user_id == viewer_user_id, NoticeRead.notice_id.in_(notice_ids))
            .all()
        }

        class_name_map = self._class_name_map(class_ids)
        teacher_map = self._teacher_name_map([notice.teacher_id for notice in notices])
        return [
            self._to_feed_item(notice, class_name_map, teacher_map, notice.id in read_ids)
            for notice in notices
        ]

    def _class_name_map(self, class_ids: list[int]) -> dict[int, str]:
        rows = (
            self.db.query(TeachingClass.id, TeachingClass.name)
            .filter(TeachingClass.id.in_(class_ids), TeachingClass.deleted_at.is_(None))
            .all()
        )
        return {row.id: row.name for row in rows}

    def _teacher_name_map(self, teacher_ids: list[int]) -> dict[int, str]:
        rows = (
            self.db.query(User.id, User.display_name)
            .filter(User.id.in_(teacher_ids), User.role == UserRole.TEACHER)
            .all()
        )
        return {row.id: row.display_name for row in rows}

    def _notice_class_links(self, notice_id: int) -> list[NoticeClass]:
        return self.db.query(NoticeClass).filter(NoticeClass.notice_id == notice_id).all()

    def _to_list_item(self, notice: Notice) -> NoticeListItem:
        links = self._notice_class_links(notice.id)
        class_ids = [link.class_id for link in links]
        class_name_map = self._class_name_map(class_ids)
        return NoticeListItem(
            id=notice.id,
            title=notice.title,
            content=notice.content,
            class_ids=class_ids,
            class_names=[class_name_map.get(class_id, f"班级{class_id}") for class_id in class_ids],
            created_at=notice.created_at,
        )

    def _to_feed_item(
        self,
        notice: Notice,
        class_name_map: dict[int, str],
        teacher_map: dict[int, str],
        is_read: bool = False,
    ) -> NoticeFeedItem:
        links = self._notice_class_links(notice.id)
        class_names = [class_name_map.get(link.class_id, f"班级{link.class_id}") for link in links]
        return NoticeFeedItem(
            id=notice.id,
            title=notice.title,
            content=notice.content,
            class_names=class_names,
            teacher_name=teacher_map.get(notice.teacher_id, "授课教师"),
            created_at=notice.created_at,
            is_read=is_read,
        )
