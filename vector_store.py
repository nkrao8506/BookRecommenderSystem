"""
FAISS-backed vector store for semantic book retrieval.

Persists to two files next to the SQLite knowledge base:
  - <path>.index      the FAISS index itself
  - <path>.ids.json   ordered list of book_ids, matching index row order

Kept intentionally simple (flat index, exact search) since the dataset
here is small (tens of thousands of books at most). At that scale a
flat index is fast enough and gives exact nearest neighbors instead of
the approximate results you'd get from IVF/HNSW - no reason to pay that
complexity cost yet. If the catalog grew into the millions, swapping
IndexFlatIP for IndexIVFFlat or HNSW would be the next step, and the
rest of this class's interface wouldn't need to change.
"""
import json
import os

import faiss
import numpy as np


class VectorStore:
    def __init__(self, dim: int, path: str = "book_vectors"):
        self.dim = dim
        self.index_path = f"{path}.index"
        self.ids_path = f"{path}.ids.json"
        self.ids: list[str] = []
        self.index = faiss.IndexFlatIP(dim)
        self._load_if_exists()

    def _load_if_exists(self):
        if os.path.exists(self.index_path) and os.path.exists(self.ids_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.ids_path) as f:
                self.ids = json.load(f)

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.ids_path, "w") as f:
            json.dump(self.ids, f)

    def clear(self):
        self.index = faiss.IndexFlatIP(self.dim)
        self.ids = []

    def add(self, ids: list[str], vectors: np.ndarray):
        assert len(ids) == vectors.shape[0], "ids and vectors must be the same length"
        self.index.add(vectors.astype("float32"))
        self.ids.extend(ids)

    def search(self, query_vector: np.ndarray, k: int = 10, exclude_ids: set[str] | None = None) -> list[tuple[str, float]]:
        """Returns up to k (book_id, cosine_similarity) pairs, best first."""
        if self.index.ntotal == 0:
            return []
        exclude_ids = exclude_ids or set()
        # Over-fetch a bit so we still have k results left after filtering exclusions.
        fetch_k = min(self.index.ntotal, k + len(exclude_ids))
        scores, indices = self.index.search(query_vector.reshape(1, -1).astype("float32"), fetch_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            book_id = self.ids[idx]
            if book_id in exclude_ids:
                continue
            results.append((book_id, float(score)))
            if len(results) >= k:
                break
        return results

    def is_empty(self) -> bool:
        return self.index.ntotal == 0