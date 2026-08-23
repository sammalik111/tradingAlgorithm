from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from trading_backend.db.base import Base
from trading_backend.models.enums import SourceCode
from trading_backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A public data provider a trade disclosure was scraped from.

    Kept separate from `CanonicalTrade` so raw data always stays attributable
    to where it came from, even after multiple sources are collapsed into a
    single canonical trade.
    """

    __tablename__ = "sources"

    code: Mapped[SourceCode] = mapped_column(Enum(SourceCode, name="source_code"), unique=True)
    display_name: Mapped[str] = mapped_column(String(128))
    base_url: Mapped[str] = mapped_column(String(512))
