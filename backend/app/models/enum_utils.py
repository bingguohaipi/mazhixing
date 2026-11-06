import enum

from sqlalchemy import Enum


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_cls]


def mysql_enum(enum_cls: type[enum.Enum], **kwargs) -> Enum:
    """Map Python str enums to MySQL ENUM values (lowercase / localized strings)."""
    return Enum(enum_cls, values_callable=enum_values, **kwargs)
