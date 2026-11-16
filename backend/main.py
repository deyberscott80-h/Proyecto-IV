from __future__ import annotations

import os
import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

DEFAULT_DB = Path(__file__).with_name("reviews_demo.sqlite3")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT NOT NULL DEFAULT ''
                CHECK (length(trim(comment)) <= 1000),
                published_at TEXT NOT NULL,
                visible INTEGER NOT NULL DEFAULT 1 CHECK (visible IN (0,1)),
                response TEXT,
                replied_at TEXT
            )
        """)
        conn.commit()



class ReviewInput(BaseModel):
    user_name: str = Field(min_length=2, max_length=100)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)

    @field_validator("user_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        result = value.strip()
        if len(result) < 2:
            raise ValueError("Must contain at least 2 characters")
        return result

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str) -> str:
        return value.strip()


class ReplyInput(BaseModel):
    response: str = Field(min_length=3, max_length=1000)

    @field_validator("response")
    @classmethod
    def check_response(cls, value: str) -> str:
        result = value.strip()
        if len(result) < 3:
            raise ValueError("Response must contain at least 3 characters")
        return result


class VisibilityInput(BaseModel):
    visible: bool


class Review(BaseModel):
    id: int
    user_name: str
    rating: int
    comment: str
    published_at: str
    visible: bool
    response: str | None
    replied_at: str | None


class Stats(BaseModel):
    total_comments: int
    visible_comments: int
    hidden_comments: int
    answered_comments: int
    average_rating: float


def create_app(db_path: Path | None = None) -> FastAPI:
    path = db_path or Path(os.getenv("REVIEWS_DB_PATH", str(DEFAULT_DB)))

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        init_database(path)
        yield

    app = FastAPI(title="Reseñas - Demo Independiente", version="1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    def connect():
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_one(review_id: int) -> dict:
        with closing(connect()) as conn:
            row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="Review not found")
        return dict(row) | {"visible": bool(row["visible"])}

    @app.get("/api/reviews", response_model=list[Review])
    def list_reviews():
        with closing(connect()) as conn:
            rows = conn.execute("SELECT * FROM reviews ORDER BY published_at DESC, id DESC").fetchall()
        return [dict(r) | {"visible": bool(r["visible"])} for r in rows]

    @app.get("/api/reviews/stats", response_model=Stats)
    def stats():
        with closing(connect()) as conn:
            row = conn.execute("""
                SELECT COUNT(*) AS total_comments,
                    COALESCE(SUM(visible), 0) AS visible_comments,
                    COALESCE(SUM(CASE WHEN visible=0 THEN 1 ELSE 0 END), 0) AS hidden_comments,
                    COALESCE(SUM(CASE WHEN response IS NOT NULL THEN 1 ELSE 0 END), 0) AS answered_comments,
                    COALESCE(ROUND(AVG(rating), 2), 0) AS average_rating
                FROM reviews
            """).fetchone()
        return dict(row)

    @app.post("/api/reviews", response_model=Review, status_code=201)
    def create_review(payload: ReviewInput):
        with closing(connect()) as conn:
            cursor = conn.execute(
                "INSERT INTO reviews(user_name,rating,comment,published_at) VALUES(?,?,?,?)",
                (payload.user_name, payload.rating, payload.comment, now_utc()),
            )
            conn.commit()
            review_id = cursor.lastrowid
        return get_one(review_id)

    @app.patch("/api/reviews/{review_id}/reply", response_model=Review)
    def reply(review_id: int, payload: ReplyInput):
        get_one(review_id)
        with closing(connect()) as conn:
            conn.execute("UPDATE reviews SET response=?, replied_at=? WHERE id=?",
                         (payload.response, now_utc(), review_id))
            conn.commit()
        return get_one(review_id)

    @app.patch("/api/reviews/{review_id}/visibility", response_model=Review)
    def visibility(review_id: int, payload: VisibilityInput):
        get_one(review_id)
        with closing(connect()) as conn:
            conn.execute("UPDATE reviews SET visible=? WHERE id=?", (int(payload.visible), review_id))
            conn.commit()
        return get_one(review_id)

    @app.delete("/api/reviews/{review_id}", status_code=204)
    def delete(review_id: int):
        get_one(review_id)
        with closing(connect()) as conn:
            conn.execute("DELETE FROM reviews WHERE id=?", (review_id,))
            conn.commit()
        return None

    return app


app = create_app()
