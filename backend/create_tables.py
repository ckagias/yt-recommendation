"""One-off script: creates all tables in Postgres from the SQLAlchemy models."""

from app.db import Base, engine
from app.models import channel, video, trending_snapshot  # noqa: F401  (import registers the models on Base)

Base.metadata.create_all(engine)
print("Tables created.")
