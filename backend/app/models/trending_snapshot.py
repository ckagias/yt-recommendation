from datetime import date

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.video import Video


class TrendingSnapshot(Base):
    __tablename__ = "trending_snapshots"
    __table_args__ = (UniqueConstraint("video_id", "country", "trending_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.video_id"))
    country: Mapped[str]
    trending_date: Mapped[date]
    view_count: Mapped[int]
    like_count: Mapped[int]
    comment_count: Mapped[int]

    video: Mapped["Video"] = relationship()
