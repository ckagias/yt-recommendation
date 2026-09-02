from fastapi import FastAPI
from sqlalchemy import text

from app.db import engine

app = FastAPI(title="YouTube Recommendation System")


@app.get("/")
def health_check():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
