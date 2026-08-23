from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from trading_workers.db.base import Base
from trading_workers.models.enums import Chamber
from trading_workers.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Politician(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "politicians"

    full_name: Mapped[str] = mapped_column(String(256))
    normalized_name: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    chamber: Mapped[Chamber] = mapped_column(Enum(Chamber, name="chamber"))
    party: Mapped[str | None] = mapped_column(String(32), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    bioguide_id: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
