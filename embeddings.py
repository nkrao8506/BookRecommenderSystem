"""
Embedding generation for the Knowledge Base.

Uses a local sentence-transformers model so semantic search doesn't
depend on an external embeddings API (no extra cost, no extra latency,
works even if the LLM provider is down).
"""
import numpy as np
from sentence_transformers import SentenceTransformer

# 384-dim, ~80MB, fast on CPU. Good default for short-text semantic search.
_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Embed a list of texts and L2-normalize each vector so that a plain
    inner product between two vectors equals their cosine similarity.
    This lets the vector store use faiss.IndexFlatIP (fast) instead of
    having to normalize at search time.
    """
    model = get_model()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    return vectors / norms


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]


def get_embedding_dim() -> int:
    """Works across sentence-transformers versions: newer releases renamed
    get_sentence_embedding_dimension() to get_embedding_dimension()."""
    model = get_model()
    if hasattr(model, "get_embedding_dimension"):
        return model.get_embedding_dimension()
    return model.get_sentence_embedding_dimension()


def book_text_for_embedding(title: str, authors: str, description: str | None, genres: list[str] | None) -> str:
    """
    Build the text we actually embed for a book. Description carries the most
    semantic signal, but title/authors/genres still help when description is
    missing (common in the Book-Crossing dataset).
    """
    parts = [title or "", authors or ""]
    if genres:
        parts.append(", ".join(genres))
    if description:
        parts.append(description)
    return " | ".join(p for p in parts if p)