from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from trading_workers.db.base import Base
from trading_workers.models.enums import SourceCode
from trading_workers.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sources"

    code: Mapped[SourceCode] = mapped_column(Enum(SourceCode, name="source_code"), unique=True)
    display_name: Mapped[str] = mapped_column(String(128))
    base_url: Mapped[str] = mapped_column(String(512))
