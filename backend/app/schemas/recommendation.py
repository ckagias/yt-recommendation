from pydantic import BaseModel


class RecommendedVideo(BaseModel):
    video_id: str
    title: str
    channel_title: str
    category: str | None
    similarity: float
    reason: str


class RecommendResponse(BaseModel):
    source_video_id: str
    source_title: str
    results: list[RecommendedVideo]
