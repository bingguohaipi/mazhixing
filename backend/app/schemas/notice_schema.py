from datetime import datetime

from pydantic import BaseModel, Field


class NoticeCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)
    class_ids: list[int] = Field(..., min_length=1)


class NoticeListItem(BaseModel):
    id: int
    title: str
    content: str
    class_ids: list[int]
    class_names: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class NoticeFeedItem(BaseModel):
    id: int
    title: str
    content: str
    class_names: list[str]
    teacher_name: str
    created_at: datetime
    is_read: bool = False

    model_config = {"from_attributes": True}


class NoticeMarkReadRequest(BaseModel):
    notice_id: int = Field(..., ge=1)
