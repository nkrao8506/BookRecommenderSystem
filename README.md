# LLM-Powered Book Recommender System

A modern, fast, and intelligent book recommendation engine that combines **semantic vector search** with **LLM-based reasoning** (a proper RAG pipeline) over an incrementally updating SQLite Knowledge Base. The backend is built using [FastAPI](https://fastapi.tiangolo.com/).

---

## 📝 Summary

> Built an LLM-powered book recommender, evolving it from keyword/random candidate selection into a full RAG pipeline: local sentence-transformer embeddings (all-MiniLM-L6-v2) indexed in FAISS for semantic retrieval, reranked and explained by Google Gemini, served via FastAPI with a Next.js/Tailwind frontend. Built a leave-one-out evaluation harness (Precision/Recall/NDCG@10) showing FAISS retrieval achieved 126x higher Recall@10 than random sampling (7.55% vs 0.06%).

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

### 7. (Optional) Evaluate Retrieval Quality
Run an offline evaluation comparing FAISS semantic retrieval against the old random-sampling baseline, using Precision@k, Recall@k, and NDCG@k:
```bash
python eval.py --k 10
```
*Note: the default demo sample (100 books, 500 ratings) is too small for this to find eligible test users, since Books.csv and Ratings.csv are sliced independently and rarely overlap at that size. Increase the `.head(N)` limits in `load_data.py`, rerun `load_data.py` and `build_index.py`, then run `eval.py` again. A few thousand books/ratings is enough to get a meaningful number of holdout cases.*

## 📊 Evaluation Results

Leave-one-out evaluation on a ~3,000-book / 20,000-rating sample (331 eligible holdout users), comparing FAISS semantic retrieval against the random-sampling baseline it replaced:

| Metric       | FAISS (semantic) | Random baseline | Lift     |
|--------------|-------------------|------------------|----------|
| Precision@10 | 0.0076            | 0.0001           | +0.0075  |
| Recall@10    | 0.0755            | 0.0006           | +0.0749  |
| NDCG@10      | 0.0429            | 0.0002           | +0.0427  |

**Reading these numbers:**
- **~126x lift in Recall@10** — the number to lead with. FAISS finds the correct held-out book over two orders of magnitude more often than random sampling, from just a user's remaining liked books as context.
- The random baseline's Recall@10 (0.0006) lands almost exactly at the theoretical hit rate (k / catalog size), which is a sanity check that the evaluation harness itself is unbiased.
- NDCG@10 ÷ Recall@10 works out to roughly rank 2-3 on average — when the target *is* retrieved, it's usually landing near the top of the top-10, not barely squeaking in.
- Book-Crossing's `Books.csv` has no real description field, so retrieval here is running on title + author alone. A 126x lift off that little signal is a strong result, with an easy next step being to enrich with real book descriptions (e.g. via the Open Library or Google Books API) for a likely further gain.

*Reproduce with `python eval.py --k 10` after loading a larger sample (see step 7 above).*

### 8. Run the Application
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
7. **Evaluation (`eval.py`):** Offline leave-one-out evaluation of the retrieval step. For each user with enough liked books, one is held out and the rest used as a query; Precision@k, Recall@k, and NDCG@k measure how often (and how highly) the held-out book gets retrieved, compared against the random-sampling baseline it replaced.

**Why retrieval before generation matters:** an LLM given the *entire* catalog can't reason well and costs a fortune in tokens. Given a *random* sample, it can only rerank whatever happened to be sampled — most of the catalog is invisible to it. Semantic retrieval narrows the field to books that are actually relevant first, so the LLM's reasoning is spent on a shortlist worth reasoning about.