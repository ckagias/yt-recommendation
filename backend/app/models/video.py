from datetime import datetime

from sqlalchemy import ARRAY, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.channel import Channel


class Video(Base):
    __tablename__ = "videos"

    video_id: Mapped[str] = mapped_column(primary_key=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.channel_id"))
    title: Mapped[str]
    description: Mapped[str]
    category: Mapped[str | None]
    tags: Mapped[list[str]] = mapped_column(ARRAY(String))
    duration_seconds: Mapped[int]
    published_at: Mapped[datetime]

    channel: Mapped["Channel"] = relationship()
