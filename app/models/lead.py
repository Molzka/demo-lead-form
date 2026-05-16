from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(60), nullable=False)
    service: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    utm_source: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    utm_campaign: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="сайт", nullable=False)
