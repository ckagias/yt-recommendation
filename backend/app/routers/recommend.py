from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.video import Video
from app.schemas.recommendation import RecommendResponse, RecommendedVideo

router = APIRouter()


def explain_match(source: Video, candidate: Video) -> str:
    reasons = []
    if source.channel_id == candidate.channel_id:
        reasons.append("same channel")
    if source.category and source.category == candidate.category:
        reasons.append(f"same category ({source.category})")
    shared_tags = set(source.tags) & set(candidate.tags)
    if shared_tags:
        sample = ", ".join(sorted(shared_tags)[:3])
        reasons.append(f"shared tags: {sample}")
    return "; ".join(reasons) if reasons else "similar title/description content"


@router.get("/recommend/{video_id}", response_model=RecommendResponse)
def recommend(video_id: str, limit: int = 10, category: str | None = None):
    session: Session = SessionLocal()
    try:
        source = session.get(Video, video_id)
        if source is None:
            raise HTTPException(status_code=404, detail="Video not found")
        if source.embedding is None:
            raise HTTPException(status_code=422, detail="Video has no embedding yet")

        distance = Video.embedding.cosine_distance(source.embedding)
        stmt = select(Video, distance.label("distance")).where(Video.video_id != video_id)
        if category is not None:
            stmt = stmt.where(Video.category == category)
        stmt = stmt.order_by(distance).limit(limit)
        rows = session.execute(stmt).all()

        results = [
            RecommendedVideo(
                video_id=candidate.video_id,
                title=candidate.title,
                channel_title=candidate.channel.title,
                category=candidate.category,
                similarity=round(1 - dist, 4),
                reason=explain_match(source, candidate),
            )
            for candidate, dist in rows
        ]

        return RecommendResponse(
            source_video_id=source.video_id,
            source_title=source.title,
            results=results,
        )
    finally:
        session.close()
