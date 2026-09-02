"""Loads youtube_trending_3_countries.csv into Postgres.

Streams the CSV row by row (never loads the whole file into memory) and
accumulates rows into batches, flushed with a single bulk upsert statement
per table per batch rather than one round-trip per row. This is the
difference between ~450K individual INSERT/SELECT pairs and ~90 bulk
statements, which is what actually makes ingestion fast.

Usage: python ingest.py [--limit N]
"""

import argparse
import csv
from datetime import date, datetime
from pathlib import Path

import isodate
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import SessionLocal
from app.models.channel import Channel
from app.models.trending_snapshot import TrendingSnapshot
from app.models.video import Video

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "youtube_trending_3_countries.csv"
BATCH_SIZE = 5000


def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_duration_seconds(value: str) -> int:
    try:
        return int(isodate.parse_duration(value).total_seconds())
    except (ValueError, TypeError, isodate.ISO8601Error):
        return 0


def parse_tags(value: str) -> list[str]:
    if not value:
        return []
    return [t.strip() for t in value.split(",") if t.strip()]


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_trending_date(value: str) -> date:
    year, month, day = value.split(".")
    return date(int(year), int(month), int(day))


def upsert_channels(session, rows: list[dict]) -> None:
    if not rows:
        return
    stmt = pg_insert(Channel).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["channel_id"],
        set_={c: stmt.excluded[c] for c in rows[0] if c != "channel_id"},
    )
    session.execute(stmt)


def upsert_videos(session, rows: list[dict]) -> None:
    if not rows:
        return
    stmt = pg_insert(Video).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["video_id"],
        set_={c: stmt.excluded[c] for c in rows[0] if c != "video_id"},
    )
    session.execute(stmt)


def insert_snapshots(session, rows: list[dict]) -> None:
    if not rows:
        return
    stmt = pg_insert(TrendingSnapshot).values(rows)
    # A snapshot is immutable once recorded for a given (video, country, day) —
    # a repeat of the same combination is a duplicate row, not new information.
    stmt = stmt.on_conflict_do_nothing(index_elements=["video_id", "country", "trending_date"])
    session.execute(stmt)


def main(limit: int | None) -> None:
    session = SessionLocal()

    seen_channels: set[str] = set()
    seen_videos: set[str] = set()
    channel_batch: list[dict] = []
    video_batch: list[dict] = []
    snapshot_batch: list[dict] = []

    rows_processed = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit is not None and rows_processed >= limit:
                break

            channel_id = row["channel_id"]
            if channel_id not in seen_channels:
                channel_batch.append(
                    dict(
                        channel_id=channel_id,
                        title=row["channel_title"] or "Unknown",
                        description=row["channel_description"] or "",
                        custom_url=row["channel_custom_url"] or None,
                        country=row["channel_country"] or None,
                        published_at=parse_datetime(row["channel_published_at"]),
                        subscriber_count=parse_int(row["channel_subscriber_count"]),
                        view_count=parse_int(row["channel_view_count"]),
                        video_count=parse_int(row["channel_video_count"]),
                    )
                )
                seen_channels.add(channel_id)

            video_id = row["video_id"]
            if video_id not in seen_videos:
                video_batch.append(
                    dict(
                        video_id=video_id,
                        channel_id=channel_id,
                        title=row["video_title"] or "Untitled",
                        description=row["video_description"] or "",
                        category=row["video_category_id"] or None,
                        tags=parse_tags(row["video_tags"]),
                        duration_seconds=parse_duration_seconds(row["video_duration"]),
                        published_at=parse_datetime(row["video_published_at"]),
                    )
                )
                seen_videos.add(video_id)

            snapshot_batch.append(
                dict(
                    video_id=video_id,
                    country=row["video_trending_country"],
                    trending_date=parse_trending_date(row["video_trending__date"]),
                    view_count=parse_int(row["video_view_count"]),
                    like_count=parse_int(row["video_like_count"]),
                    comment_count=parse_int(row["video_comment_count"]),
                )
            )

            rows_processed += 1
            if rows_processed % BATCH_SIZE == 0:
                # Channels and videos must land before the snapshots that
                # reference them, since trending_snapshots has foreign keys
                # into both.
                upsert_channels(session, channel_batch)
                upsert_videos(session, video_batch)
                insert_snapshots(session, snapshot_batch)
                session.commit()
                channel_batch, video_batch, snapshot_batch = [], [], []
                print(f"{rows_processed} rows processed…")

    upsert_channels(session, channel_batch)
    upsert_videos(session, video_batch)
    insert_snapshots(session, snapshot_batch)
    session.commit()
    session.close()
    print(f"Done. {rows_processed} rows processed, {len(seen_channels)} channels, {len(seen_videos)} videos.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N rows")
    args = parser.parse_args()
    main(args.limit)
