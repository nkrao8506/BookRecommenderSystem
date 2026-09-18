# LLM-Powered Book Recommender System

A modern, fast, and intelligent book recommendation engine that combines **semantic vector search** with **LLM-based reasoning** (a proper RAG pipeline) over an incrementally updating SQLite Knowledge Base. The backend is built using [FastAPI](https://fastapi.tiangolo.com/).

> **Note on Frontend:** The previous Next.js frontend (in the `web/` directory) is currently undergoing a rewrite to integrate with this new LLM-powered backend. It is preserved but may not function out-of-the-box until updated.

---

## 🚀 Features

- **Semantic Retrieval:** Book descriptions are embedded locally (sentence-transformers) and indexed in a FAISS vector store, so candidate selection is driven by actual meaning instead of keyword matching or random sampling.
- **LLM-Based Reasoning:** The retrieved candidates are handed to an LLM, which reranks them and writes a rationale for each pick — retrieval finds *what's relevant*, the LLM explains *why*.
- **Dynamic Knowledge Base:** Stores books, users, and interactions (ratings, reviews) in a local SQLite database that grows over time.
- **Natural Language Preferences:** Supports querying book recommendations based on free-form text input (e.g., "I want a fantasy novel with political intrigue") — the query is embedded and matched directly against the vector index.
- **Fast & Interactive API:** Built with FastAPI, providing automatic interactive API documentation via Swagger UI.

## 🛠️ Tech Stack

- **Backend:** Python 3, FastAPI, Uvicorn, Pydantic
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`, local, no external API calls)
- **Vector Store:** FAISS (`IndexFlatIP`, exact cosine similarity search)
- **LLM Integration:** Google Gemini (`gemini-2.5-flash`) for reranking and rationale generation
- **Database:** SQLite3 (Local Knowledge Base)
- **Data Processing:** Pandas (for initial data seeding)

---

## 📦 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/nkrao8506/BookRecommenderSystem.git
cd BookRecommenderSystem
```

### 2. Set up Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory and add your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Initialize the Knowledge Base
To populate the SQLite database with the initial dataset (`Books.csv` and `Ratings.csv`):
```bash
python load_data.py
```
*This will create a `knowledge_base.db` file in your project root.*

### 6. Build the Vector Index
Embed the catalog and build the FAISS index used for semantic retrieval:
```bash
python build_index.py
```
*This will create `book_vectors.index` and `book_vectors.ids.json`. The first run downloads the embedding model (~80MB). Re-run this any time the catalog changes, or if you switch embedding models.*

### 7. Run the Application
Start the FastAPI server:
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

---

## 📡 API Endpoints

Once the server is running, you can interact with the API directly or visit **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** for the interactive Swagger UI.

### Core Endpoints:
- `GET /` - Root status/welcome message.
- `GET /books/popular` - Get a list of popular books.
- `GET /users/{user_id}/recommendations` - Get personalized recommendations based on a user's reading history.
- `GET /books/{book_id}/similar` - Find books similar to a specific title.
- `POST /recommendations/free-text` - Request recommendations using natural language preferences.
- `POST /books` - Add a new book to the Knowledge Base.
- `POST /interactions` - Add a user rating/review interaction.

---

## 🧠 System Architecture Details

This is a standard **RAG (Retrieval-Augmented Generation)** pipeline applied to recommendations:

1. **Knowledge Base (`knowledge_base.py`):** Long-term storage. SQLite database (`knowledge_base.db`) holding book metadata and user interactions.
2. **Embeddings (`embeddings.py`):** Turns a book's title/authors/genres/description (or a user's free-text query) into a normalized vector using a local sentence-transformers model.
3. **Vector Store (`vector_store.py`):** A FAISS index mapping book vectors → book ids, persisted to disk. This is the "retrieval" half of RAG.
4. **Indexing (`build_index.py`):** One-off/rerunnable script that embeds the full catalog from the Knowledge Base and writes the FAISS index.
5. **Recommender Core (`recommender.py`):** Builds a query (from a user's liked books, free text, or a target book), retrieves the top semantically-similar candidates from the vector store, then hands that shortlist to the LLM to rerank and explain. This is the "generation/reasoning" half of RAG. If the index hasn't been built yet, it falls back to the old keyword/random candidate selection so the API doesn't break.
6. **API Layer (`main.py`):** FastAPI application exposing clean, documented REST HTTP endpoints.

**Why retrieval before generation matters:** an LLM given the *entire* catalog can't reason well and costs a fortune in tokens. Given a *random* sample, it can only rerank whatever happened to be sampled — most of the catalog is invisible to it. Semantic retrieval narrows the field to books that are actually relevant first, so the LLM's reasoning is spent on a shortlist worth reasoning about.