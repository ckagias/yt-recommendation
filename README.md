# YT Recommendation System

### A content-based video recommendation API built with FastAPI, PostgreSQL, and pgvector

[About](#about) • [How it works](#how-it-works) • [Installation](#installation) • [Project layout](#project-layout) • [Dependencies](#dependencies) • [Status](#status) • [License](#license)

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
5. **Start the API**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. Visit `http://localhost:8000` — it should return `{"status": "ok", "database": "connected"}`.

No `.env` file is required for local development; `docker-compose.yml` and the backend's default database URL already agree with each other out of the box.

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

---

## Status

Core pipeline is working end to end: the real trending-videos dataset (~37k videos, ~450k trending snapshots) is loaded into PostgreSQL, every video has a pgvector embedding, and `GET /recommend/{video_id}` returns ranked, explained recommendations backed by real cosine-similarity search. Still to build: an `/explain`-only endpoint for a specific video pair, request/response validation edge cases, and tests.

---

## License

This project is licensed under the [MIT License](LICENSE).
