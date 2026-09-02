from fastapi import FastAPI
from sqlalchemy import text

from app.db import engine
from app.routers import recommend

app = FastAPI(title="YouTube Recommendation System")
app.include_router(recommend.router)


@app.get("/")
def health_check():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
