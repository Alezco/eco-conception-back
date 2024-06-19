# models.py
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

class Movie(BaseModel):
    id: int
    title: str
    genre: str

class Review(BaseModel):
    movie_id: int
    rating: float
    comment: str

def get_db_connection():
    conn = sqlite3.connect('test.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS movies (
                            id INTEGER PRIMARY KEY,
                            title TEXT NOT NULL,
                            genre TEXT NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
                            id INTEGER PRIMARY KEY,
                            movie_id INTEGER,
                            rating REAL,
                            comment TEXT,
                            FOREIGN KEY (movie_id) REFERENCES movies (id))''')

init_db()

def get_movies(page: int = 1, limit: int = 10) -> List[Movie]:
    offset = (page - 1) * limit
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM movies LIMIT ? OFFSET ?', (limit, offset))
        return [Movie(**row) for row in cursor.fetchall()]

def get_movie(id: int) -> Optional[Movie]:
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM movies WHERE id = ?', (id,))
        row = cursor.fetchone()
        return Movie(**row) if row else None

def create_review(review: Review) -> Review:
    with get_db_connection() as conn:
        conn.execute('INSERT INTO reviews (movie_id, rating, comment) VALUES (?, ?, ?)',
                     (review.movie_id, review.rating, review.comment))
        conn.commit()
        return review

def get_recommendations() -> List[Movie]:
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM movies ORDER BY RANDOM() LIMIT 5')
        return [Movie(**row) for row in cursor.fetchall()]
