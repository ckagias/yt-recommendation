from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Channel(Base):
    __tablename__ = "channels"

    channel_id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    custom_url: Mapped[str | None]
    country: Mapped[str | None]
    published_at: Mapped[datetime]
    subscriber_count: Mapped[int] = mapped_column(BigInteger)
    view_count: Mapped[int] = mapped_column(BigInteger)
    video_count: Mapped[int]
