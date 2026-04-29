import os
import json
import requests
from typing import List, Dict, Any
from knowledge_base import KnowledgeBase, Book

class OpenRouterClient:
    def __init__(self, api_key: str = None, model: str = "anthropic/claude-3-haiku"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        if not self.api_key:
             print("Warning: OPENROUTER_API_KEY not set")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Book Recommender System",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error calling OpenRouter: {e}")
            if hasattr(response, 'text'):
                 print(f"Response: {response.text}")
            return "{}"

class LLMRecommender:
    def __init__(self, kb: KnowledgeBase, llm_client: OpenRouterClient):
        self.kb = kb
        self.llm = llm_client

    def recommend_for_user(self, user_id: str, n: int = 10) -> List[Dict]:
        profile = self.kb.get_user_profile(user_id)
        if not profile.interactions:
            return self._recommend_popular(n)

        # Basic retrieve: just get recent books user liked + some candidates
        # In a real system, use embeddings here
        candidates = self.kb.search_books(limit=100) 
        
        system_prompt = """
        You are an expert book recommender system. Given a user's reading history and a list of candidate books,
        recommend the best books for them. Return ONLY valid JSON matching this schema:
        {
          "recommendations": [
             {"book_id": "id", "title": "Title", "rationale": "Short explanation of why"}
          ]
        }
        """

        user_history = [{"book_id": i.book_id, "rating": i.rating} for i in profile.interactions]
        candidates_json = [{"id": c.id, "title": c.title, "authors": c.authors} for c in candidates]
        
        user_prompt = f"User History:\n{json.dumps(user_history)}\n\nCandidates:\n{json.dumps(candidates_json)}\n\nProvide {n} recommendations."

        response_str = self.llm.generate(system_prompt, user_prompt)
        try:
            result = json.loads(response_str)
            return result.get("recommendations", [])
        except:
            return []

    def recommend_from_free_text(self, preference_text: str, n: int = 10) -> List[Dict]:
        candidates = self.kb.search_books(limit=100)
        
        system_prompt = """
        You are an expert book recommender system. Given a user's free text preference and a list of candidate books,
        recommend the best books for them. Return ONLY valid JSON matching this schema:
        {
          "recommendations": [
             {"book_id": "id", "title": "Title", "rationale": "Short explanation of why"}
          ]
        }
        """
        
        candidates_json = [{"id": c.id, "title": c.title, "authors": c.authors} for c in candidates]
        user_prompt = f"Preferences:\n{preference_text}\n\nCandidates:\n{json.dumps(candidates_json)}\n\nProvide {n} recommendations."

        response_str = self.llm.generate(system_prompt, user_prompt)
        try:
            result = json.loads(response_str)
            return result.get("recommendations", [])
        except:
            return []

    def recommend_similar_to_book(self, book_id: str, n: int = 10) -> List[Dict]:
        book = self.kb.get_book(book_id)
        if not book:
            return []
            
        candidates = self.kb.search_books(limit=100)
        
        system_prompt = """
        You are an expert book recommender system. Given a target book and a list of candidate books,
        recommend the most similar books. Return ONLY valid JSON matching this schema:
        {
          "recommendations": [
             {"book_id": "id", "title": "Title", "rationale": "Short explanation of why"}
          ]
        }
        """
        
        candidates_json = [{"id": c.id, "title": c.title, "authors": c.authors} for c in candidates]
        user_prompt = f"Target Book:\n{book.json()}\n\nCandidates:\n{json.dumps(candidates_json)}\n\nProvide {n} similar books."

        response_str = self.llm.generate(system_prompt, user_prompt)
        try:
            result = json.loads(response_str)
            return result.get("recommendations", [])
        except:
            return []

    def _recommend_popular(self, n: int = 10) -> List[Dict]:
        # Fallback
        books = self.kb.search_books(limit=n)
        return [{"book_id": b.id, "title": b.title, "rationale": "Popular book"} for b in books]
