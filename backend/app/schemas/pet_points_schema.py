from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PointLedgerTypeLiteral = Literal["EARN_FIRST_AC", "SPEND_SHOP", "ADMIN_ADJUST"]
PointLedgerRefTypeLiteral = Literal["problem", "shop_order", "admin"]


class StudentPointsSummary(BaseModel):
    balance: int
    total_earned: int
    total_spent: int
    first_ac_count: int


class PointLedgerItem(BaseModel):
    id: int
    type: PointLedgerTypeLiteral
    delta: int
    balance_after: int
    ref_type: PointLedgerRefTypeLiteral | None
    ref_id: int | None
    ref_title: str | None
    created_at: datetime


class PointLedgerListResponse(BaseModel):
    items: list[PointLedgerItem]
    total: int
    page: int
    page_size: int
