from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.channel import Channel

# all-MiniLM-L6-v2 always produces a 384-dimensional embedding.
EMBEDDING_DIM = 384


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
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    channel: Mapped["Channel"] = relationship()
