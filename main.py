from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from knowledge_base import KnowledgeBase, Book, Interaction
from recommender import LLMRecommender, OpenRouterClient

app = FastAPI(title="LLM Book Recommender API")

kb = KnowledgeBase()
llm_client = OpenRouterClient()
recommender = LLMRecommender(kb, llm_client)

class FreeTextRequest(BaseModel):
    preference_text: str
    n: int = 10

class InteractionRequest(BaseModel):
    user_id: str
    book_id: str
    rating: float
    review_text: Optional[str] = None

@app.get("/books/popular")
def get_popular_books(n: int = 10):
    return recommender._recommend_popular(n)

@app.get("/users/{user_id}/recommendations")
def get_user_recommendations(user_id: str, n: int = 10):
    return recommender.recommend_for_user(user_id, n)

@app.get("/books/{book_id}/similar")
def get_similar_books(book_id: str, n: int = 10):
    return recommender.recommend_similar_to_book(book_id, n)

@app.post("/books")
def create_book(book: Book):
    kb.add_book(book)
    return {"status": "success"}

@app.post("/interactions")
def add_interaction(interaction: InteractionRequest):
    kb.add_interaction(
        interaction.user_id,
        interaction.book_id,
        interaction.rating,
        interaction.review_text
    )
    return {"status": "success"}

@app.post("/recommendations/free-text")
def get_free_text_recommendations(req: FreeTextRequest):
    return recommender.recommend_from_free_text(req.preference_text, req.n)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
