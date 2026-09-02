"""Generates and stores an embedding vector for every video that doesn't have one yet.

Combines title, description, tags, and category into one text blob per video
(the same "soup" idea as content-based recommenders generally use), embeds it
with a sentence-transformer model, and writes the vector back to Postgres.
"""

from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from app.db import SessionLocal
from app.models.video import Video

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 256


def build_soup(video: Video) -> str:
    parts = [video.title, video.description, video.category or "", " ".join(video.tags)]
    return " ".join(p for p in parts if p)


def main() -> None:
    model = SentenceTransformer(MODEL_NAME)
    session = SessionLocal()

    videos = session.scalars(select(Video).where(Video.embedding.is_(None))).all()
    print(f"{len(videos)} videos need embeddings.")

    for i in range(0, len(videos), BATCH_SIZE):
        batch = videos[i : i + BATCH_SIZE]
        texts = [build_soup(v) for v in batch]
        embeddings = model.encode(texts, show_progress_bar=False)

        for video, embedding in zip(batch, embeddings):
            video.embedding = embedding.tolist()

        session.commit()
        print(f"{min(i + BATCH_SIZE, len(videos))}/{len(videos)} embedded…")

    session.close()
    print("Done.")


if __name__ == "__main__":
    main()
