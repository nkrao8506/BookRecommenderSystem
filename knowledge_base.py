import json
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import os
import sqlite3

class Book(BaseModel):
    id: str
    title: str
    authors: str
    year: Optional[str] = None
    publisher: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    genres: Optional[List[str]] = None

class Interaction(BaseModel):
    user_id: str
    book_id: str
    rating: float
    review_text: Optional[str] = None

class UserProfile(BaseModel):
    user_id: str
    interactions: List[Interaction]

class KnowledgeBase:
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    authors TEXT,
                    year TEXT,
                    publisher TEXT,
                    image_url TEXT,
                    description TEXT,
                    genres TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    book_id TEXT,
                    rating REAL,
                    review_text TEXT,
                    FOREIGN KEY(book_id) REFERENCES books(id)
                )
            """)
            conn.commit()

    def get_book(self, book_id: str) -> Optional[Book]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            if row:
                return Book(
                    id=row[0], title=row[1], authors=row[2], year=row[3],
                    publisher=row[4], image_url=row[5], description=row[6],
                    genres=json.loads(row[7]) if row[7] else None
                )
        return None

    def add_book(self, book: Book):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO books (id, title, authors, year, publisher, image_url, description, genres)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                book.id, book.title, book.authors, book.year, book.publisher,
                book.image_url, book.description, json.dumps(book.genres) if book.genres else None
            ))
            conn.commit()

    def add_interaction(self, user_id: str, book_id: str, rating: float, review_text: str = None):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO interactions (user_id, book_id, rating, review_text)
                VALUES (?, ?, ?, ?)
            """, (user_id, book_id, rating, review_text))
            conn.commit()

    def get_user_profile(self, user_id: str) -> UserProfile:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT user_id, book_id, rating, review_text FROM interactions WHERE user_id = ?", (user_id,))
            interactions = [
                Interaction(user_id=r[0], book_id=r[1], rating=r[2], review_text=r[3])
                for r in cursor.fetchall()
            ]
        return UserProfile(user_id=user_id, interactions=interactions)

    def search_books(self, query: str = None, limit: int = 50) -> List[Book]:
        # Simple exact text search for now, could use embeddings later
        with self._get_conn() as conn:
            if query:
                like_query = f"%{query}%"
                cursor = conn.execute("SELECT * FROM books WHERE title LIKE ? OR authors LIKE ? LIMIT ?", (like_query, like_query, limit))
            else:
                cursor = conn.execute("SELECT * FROM books LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [
                 Book(
                    id=row[0], title=row[1], authors=row[2], year=row[3],
                    publisher=row[4], image_url=row[5], description=row[6],
                    genres=json.loads(row[7]) if row[7] else None
                ) for row in rows
            ]
