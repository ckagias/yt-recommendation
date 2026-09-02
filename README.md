# YT Recommendation System

### A content-based video recommendation API built with FastAPI, PostgreSQL, and pgvector

[About](#about) • [How it works](#how-it-works) • [Installation](#installation) • [Usage](#usage) • [Project layout](#project-layout) • [Dependencies](#dependencies) • [Status](#status) • [Limitations](#limitations) • [License](#license)

---

## About

A backend service that recommends YouTube videos based on content similarity, using real trending-video metadata rather than a toy dataset. Built around a proper relational schema (channels, videos, and time-series trending snapshots as separate tables) and served as a REST API, not a notebook.

---

## How it works

Video metadata (title, description, tags, category) is embedded into vectors using a sentence-transformer model, stored in PostgreSQL via the [pgvector](https://github.com/pgvector/pgvector) extension, and compared with cosine similarity to rank recommendations. Recommendations come with a stated reason (shared channel, overlapping tags, shared category) rather than a bare similarity score.

---

## Installation

### Requirements

- Python 3.11+
- Docker and Docker Compose

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ckagias/yt-recommendation.git
   cd yt-recommendation
   ```
2. **Start PostgreSQL (with pgvector)**
   ```bash
   docker compose up -d
   ```
3. **Install backend dependencies**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   pip install -r requirements.txt
   ```
   The `torch` line installs the CPU-only PyTorch build first. Skipping it lets
   `sentence-transformers` pull in the default GPU/CUDA build instead, which adds
   over a gigabyte of unused CUDA packages since this project only does CPU inference.
4. **Create the database tables**
   ```bash
   python create_tables.py
   ```
5. **Get the dataset**: download the [Youtube Trending Videos Dataset](https://www.kaggle.com/datasets/keshavbansal95/youtube-trending-videos-dataset)
   from Kaggle and extract `youtube_trending_3_countries.csv` into `data/` at the
   repo root (`data/youtube_trending_3_countries.csv`). Not included in the repo.
6. **Load the data into Postgres**
   ```bash
   python ingest.py
   ```
   Takes under a minute. Loads ~450k trending-snapshot rows across ~37k distinct
   videos and ~6k channels via batched upserts.
7. **Generate embeddings for every video**
   ```bash
   python generate_embeddings.py
   ```
   Downloads the `all-MiniLM-L6-v2` sentence-transformer model on first run
   (a few hundred MB, cached afterward), then embeds every video's title,
   description, tags, and category. Takes a few minutes on CPU.
8. **Start the API**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
9. Visit `http://localhost:8000`. It should return `{"status": "ok", "database": "connected"}`.

No `.env` file is required for local development; `docker-compose.yml` and the backend's default database URL already agree with each other out of the box. Steps 5-7 are one-time setup, skip them on later runs.

---

## Usage

With the server running (`uvicorn app.main:app --reload --port 8000`):

- **Interactive API docs**: open `http://localhost:8000/docs` in a browser.
  FastAPI's auto-generated Swagger UI, lets you call `/recommend` through a form
  without writing curl commands.
- **Health check**
  ```bash
  curl http://127.0.0.1:8000/
  ```
- **Get recommendations for a video**
  ```bash
  curl "http://127.0.0.1:8000/recommend/<video_id>?limit=5" | python3 -m json.tool
  ```
  Find a real `video_id` to try:
  ```bash
  docker compose exec db psql -U yt -d yt_recommender \
    -c "SELECT video_id, title FROM videos ORDER BY random() LIMIT 5;"
  ```
- **Filter recommendations by category**
  ```bash
  curl "http://127.0.0.1:8000/recommend/<video_id>?limit=5&category=Sports" | python3 -m json.tool
  ```
  Note: forcing a category the source video doesn't naturally match still
  returns results (the closest videos within that category), but similarity
  scores drop sharply since the constraint overrides genuine similarity. A
  real limitation, not a bug.
- **Explore the raw data**
  ```bash
  docker compose exec db psql -U yt -d yt_recommender
  ```
  Then, for example:
  ```sql
  SELECT category, count(*) FROM videos GROUP BY category ORDER BY count(*) DESC;
  ```

---

## Project layout

```
backend/
  app/
    main.py          FastAPI app and routes
    config.py         Settings, loaded from env vars
    db.py               SQLAlchemy engine, session factory, declarative base
    models/              Table definitions: Channel, Video, TrendingSnapshot
    schemas/               API request/response shapes: RecommendResponse, RecommendedVideo
    routers/                 recommend.py: GET /recommend/{video_id}
  create_tables.py    One-off script to create tables from the models
  ingest.py            Loads the CSV dataset into Postgres via bulk upserts
  generate_embeddings.py  Embeds every video's title/description/tags/category with
                            sentence-transformers and stores the vector via pgvector
data/                Local dataset storage (git-ignored, not included in the repo)
docker-compose.yml   PostgreSQL + pgvector for local development
```

---

## Dependencies

| Package                                                       | Purpose                                    |
| -------------------------------------------------------------- | ------------------------------------------- |
| [FastAPI](https://fastapi.tiangolo.com/)                       | Web framework                               |
| [Uvicorn](https://www.uvicorn.org/)                             | ASGI server                                 |
| [SQLAlchemy](https://www.sqlalchemy.org/)                       | ORM and database toolkit                    |
| [psycopg](https://www.psycopg.org/psycopg3/)                    | PostgreSQL driver                           |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Environment-based configuration |
| [pgvector](https://github.com/pgvector/pgvector)                | Vector similarity search inside PostgreSQL  |
| [sentence-transformers](https://www.sbert.net/)                 | Generates the video embeddings              |
| [PyTorch](https://pytorch.org/) (CPU build)                     | Backs sentence-transformers                 |
| [isodate](https://github.com/gweis/isodate)                     | Parses ISO 8601 video durations             |

---

## Status

Core pipeline is working end to end: the real trending-videos dataset (~37k videos, ~450k trending snapshots) is loaded into PostgreSQL, every video has a pgvector embedding, and `GET /recommend/{video_id}` returns ranked, explained recommendations backed by real cosine-similarity search, with bounded `limit` and an optional category filter. Still to build: an `/explain`-only endpoint for a specific video pair, and tests.

---

## Limitations

- **Cold start**: a video only shows up in `/recommend` results once it has an embedding. A newly ingested video needs `generate_embeddings.py` rerun before it's queryable, there's no on-demand embedding at request time.
- **The category filter can force weak matches**: `?category=X` restricts results to that category even when nothing in it is genuinely similar to the source video. In testing, forcing an unrelated category on an FPL transfer-tips video still returned five results, but their similarity dropped from 0.99 (same channel, same real topic) to around 0.30, the closest available options in a category that doesn't actually match. The filter narrows the search space, it doesn't validate that a good match exists within it.
- **Content-based only**: recommendations come purely from title, description, tags, and category text, embedded and compared by meaning. There's no collaborative signal (what other viewers of this video also watched), so a video with thin or generic metadata gets weaker recommendations regardless of how good the video actually is.
- **Similarity search isn't approximate yet**: pgvector runs an exact nearest-neighbor scan over all ~37k video embeddings, which is fast at this scale but doesn't use an approximate index (`ivfflat` or `hnsw`). That would need revisiting before this approach could hold up at millions of videos.

---

## License

This project is licensed under the [MIT License](LICENSE).
