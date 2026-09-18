"""
Builds (or rebuilds) the semantic search index from the books already
loaded into the Knowledge Base.

Pipeline stage 2 of 2: `load_data.py` gets CSVs into SQLite, this script
embeds that catalog into a FAISS vector store. Kept separate on purpose -
re-embedding is a different operation (slower, model-dependent) from
ingestion, and you'll want to rerun this alone whenever the embedding
model changes without re-importing the raw CSVs.

Usage:
    python build_index.py
"""
from embeddings import book_text_for_embedding, embed_texts, get_embedding_dim
from knowledge_base import KnowledgeBase
from vector_store import VectorStore


def build_index():
    kb = KnowledgeBase()
    books = kb.get_all_books()
    print(f"Loaded {len(books)} books from the knowledge base.")

    if not books:
        print("No books found. Run load_data.py first.")
        return

    texts = [
        book_text_for_embedding(b.title, b.authors, b.description, b.genres)
        for b in books
    ]
    ids = [b.id for b in books]

    print("Embedding book texts (first run downloads the model, ~80MB)...")
    vectors = embed_texts(texts)

    dim = get_embedding_dim()
    store = VectorStore(dim=dim)
    store.clear()  # full rebuild, not an incremental add
    store.add(ids, vectors)
    store.save()

    print(f"Indexed {len(ids)} books into the vector store ({store.index_path}, {store.ids_path}).")


if __name__ == "__main__":
    build_index()