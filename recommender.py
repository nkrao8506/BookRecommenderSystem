import json
import os

import requests
from dotenv import load_dotenv

from embeddings import book_text_for_embedding, embed_query, get_embedding_dim
from knowledge_base import Book, KnowledgeBase
from vector_store import VectorStore

load_dotenv()


class GoogleGeminiClient:
    def __init__(
        self,
        api_key: str = None,
        model: str = "gemini-2.5-flash",
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not set")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            response = requests.post(f"{self.base_url}?key={self.api_key}", headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            print(f"DEBUG LLM Raw Output: {content}")
            return content
        except Exception as e:
            print(f"Error calling Google Gemini API: {e}")
            if 'response' in locals() and hasattr(response, "text"):
                print(f"Response Body: {response.text}")
            return "{}"


class LLMRecommender:
    # Size of the candidate pool handed to the LLM for reranking/explanation.
    # Retrieval's job is recall (don't miss anything relevant); the LLM's job
    # is precision + rationale over that shortlist.
    CANDIDATE_POOL_SIZE = 40

    # Ratings are 0-10 in the Book-Crossing dataset; treat this and above as "liked".
    LIKED_RATING_THRESHOLD = 7

    def __init__(self, kb: KnowledgeBase, llm_client: GoogleGeminiClient):
        self.kb = kb
        self.llm = llm_client
        dim = get_embedding_dim()
        self.vector_store = VectorStore(dim=dim)
        if self.vector_store.is_empty():
            print(
                "Warning: vector index is empty. Falling back to keyword/random "
                "candidate selection until you run `python build_index.py`."
            )

    def _semantic_candidates(self, query_text: str, n: int, exclude_ids: set[str] | None = None) -> list[Book]:
        """Shared retrieval step: embed a query and pull the top-n most similar
        books from the vector store, with a graceful fallback to the old
        behavior if the index hasn't been built yet."""
        if self.vector_store.is_empty():
            return self.kb.search_books(limit=n)

        query_vector = embed_query(query_text)
        hits = self.vector_store.search(query_vector, k=n, exclude_ids=exclude_ids)
        book_ids = [book_id for book_id, _score in hits]
        return self.kb.get_books_by_ids(book_ids)

    def recommend_for_user(self, user_id: str, n: int = 10) -> list[dict]:
        profile = self.kb.get_user_profile(user_id)
        if not profile.interactions:
            return self._recommend_popular(n)

        # Build a "taste profile" query from the books the user actually liked,
        # rather than sampling the catalog at random. Books they didn't rate
        # highly don't get to shape what we retrieve.
        liked_book_ids = [
            i.book_id for i in profile.interactions
            if i.rating >= self.LIKED_RATING_THRESHOLD
        ]
        already_seen = {i.book_id for i in profile.interactions}

        if liked_book_ids:
            liked_books = self.kb.get_books_by_ids(liked_book_ids)
            profile_text = " | ".join(
                book_text_for_embedding(b.title, b.authors, b.description, b.genres)
                for b in liked_books
            )
            candidates = self._semantic_candidates(
                profile_text, self.CANDIDATE_POOL_SIZE, exclude_ids=already_seen
            )
        else:
            # User has interactions but none rated highly enough to anchor a
            # taste profile - fall back to a general candidate pool.
            candidates = self.kb.search_books(limit=self.CANDIDATE_POOL_SIZE)

        system_prompt = """
        You are an expert book recommender system. Given a user's reading history and a list of candidate books,
        recommend the best books for them. Return ONLY valid JSON matching this schema:
        {
          "recommendations": [
             {"book_id": "id", "title": "Title", "rationale": "Short explanation of why", "image": "image url if available"}
          ]
        }
        """

        user_history = [
            {"book_id": i.book_id, "rating": i.rating} for i in profile.interactions
        ]
        candidates_json = [
            {"id": c.id, "title": c.title, "authors": c.authors, "image": c.image_url} for c in candidates
        ]

        user_prompt = f"User History:\n{json.dumps(user_history)}\n\nCandidates:\n{json.dumps(candidates_json)}\n\nProvide {n} recommendations."

        response_str = self.llm.generate(system_prompt, user_prompt)
        try:
            # Handle markdown JSON wrapping if LLM returns it
            if response_str.startswith("```json"):
                response_str = response_str.split("```json")[1].rsplit("```", 1)[0].strip()
            elif response_str.startswith("```"):
                response_str = response_str.split("```")[1].rsplit("```", 1)[0].strip()

            result = json.loads(response_str)
            return result.get("recommendations", [])
        except Exception as e:
            print(f"Error parsing JSON for recommend_for_user: {e}\nResponse str: {response_str}")
            return []

    def recommend_from_free_text(self, preference_text: str, n: int = 10) -> list[dict]:
        # This is the clearest RAG case: the user's own words become the query
        # vector, retrieval finds semantically close books, the LLM explains why.
        candidates = self._semantic_candidates(preference_text, self.CANDIDATE_POOL_SIZE)

        system_prompt = """
        You are an expert book recommender system. Given a user's free text preference and a list of candidate books,
        recommend the best books for them. Return ONLY valid JSON matching this schema:
        {
          "recommendations": [
             {"book_id": "id", "title": "Title", "rationale": "Short explanation of why", "image": "image url if available"}
          ]
        }
        """

        candidates_json = [
            {"id": c.id, "title": c.title, "authors": c.authors, "image": c.image_url} for c in candidates
        ]
        user_prompt = f"Preferences:\n{preference_text}\n\nCandidates:\n{json.dumps(candidates_json)}\n\nProvide {n} recommendations."

        response_str = self.llm.generate(system_prompt, user_prompt)
        try:
            # Handle markdown JSON wrapping if LLM returns it
            if response_str.startswith("```json"):
                response_str = response_str.split("```json")[1].rsplit("```", 1)[0].strip()
            elif response_str.startswith("```"):
                response_str = response_str.split("```")[1].rsplit("```", 1)[0].strip()

            result = json.loads(response_str)
            return result.get("recommendations", [])
        except Exception as e:
            print(f"Error parsing JSON for recommend_from_free_text: {e}\nResponse str: {response_str}")
            return []

    def recommend_similar_to_book(self, book_id: str, n: int = 10) -> list[dict]:
        book = self.kb.get_book(book_id)
        if not book:
            return []

        query_text = book_text_for_embedding(book.title, book.authors, book.description, book.genres)
        candidates = self._semantic_candidates(
            query_text, self.CANDIDATE_POOL_SIZE, exclude_ids={book_id}
        )

        system_prompt = """
        You are an expert book recommender system. Given a target book and a list of candidate books,
        recommend the most similar books. Return ONLY valid JSON matching this schema:
        {
          "recommendations": [
             {"book_id": "id", "title": "Title", "rationale": "Short explanation of why", "image": "image url if available"}
          ]
        }
        """

        candidates_json = [
            {"id": c.id, "title": c.title, "authors": c.authors, "image": c.image_url} for c in candidates
        ]
        user_prompt = f"Target Book:\n{book.json()}\n\nCandidates:\n{json.dumps(candidates_json)}\n\nProvide {n} similar books."

        response_str = self.llm.generate(system_prompt, user_prompt)
        try:
            # Handle markdown JSON wrapping if LLM returns it
            if response_str.startswith("```json"):
                response_str = response_str.split("```json")[1].rsplit("```", 1)[0].strip()
            elif response_str.startswith("```"):
                response_str = response_str.split("```")[1].rsplit("```", 1)[0].strip()
                
            result = json.loads(response_str)
            return result.get("recommendations", [])
        except Exception as e:
            print(f"Error parsing JSON for recommend_similar_to_book: {e}\nResponse str: {response_str}")
            return []

    def _recommend_popular(self, n: int = 10) -> list[dict]:
        # Fallback
        books = self.kb.search_books(limit=n)
        return [
            {
                "book_id": b.id,
                "title": b.title,
                "rationale": "Popular book",
                "image": b.image_url,
            }
            for b in books
        ]