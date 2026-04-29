# LLM-Powered Book Recommender System

A modern, fast, and intelligent book recommendation engine powered by Large Language Models (LLMs) via [OpenRouter](https://openrouter.ai/) and an incrementally updating SQLite Knowledge Base. The backend is built using [FastAPI](https://fastapi.tiangolo.com/).

> **Note on Frontend:** The previous Next.js frontend (in the `web/` directory) is currently undergoing a rewrite to integrate with this new LLM-powered backend. It is preserved but may not function out-of-the-box until updated.

---

## 🚀 Features

- **LLM-Based Reasoning:** Generates personalized book recommendations and explanations using top-tier LLMs instead of static collaborative filtering models.
- **Dynamic Knowledge Base:** Stores books, users, and interactions (ratings, reviews) in a local SQLite database that grows over time.
- **Natural Language Preferences:** Supports querying book recommendations based on free-form text input (e.g., "I want a fantasy novel with political intrigue").
- **Fast & Interactive API:** Built with FastAPI, providing automatic interactive API documentation via Swagger UI.

## 🛠️ Tech Stack

- **Backend:** Python 3, FastAPI, Uvicorn, Pydantic
- **LLM Integration:** OpenRouter API (defaults to Claude 3 / Nemotron or can be configured via environment variables)
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
Create a `.env` file in the root directory and add your OpenRouter API key:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 5. Initialize the Knowledge Base
To populate the SQLite database with the initial dataset (`Books.csv` and `Ratings.csv`):
```bash
python load_data.py
```
*This will create a `knowledge_base.db` file in your project root.*

### 6. Run the Application
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

1. **Knowledge Base (`knowledge_base.py`):** Acts as the long-term memory for the system. It uses an SQLite database (`knowledge_base.db`) to store book metadata and user interactions.
2. **Recommender Core (`recommender.py`):** Handles candidate retrieval from the Knowledge Base and orchestrates the prompt construction for the LLM. It maps the LLM's structured JSON output back to the API layer.
3. **API Layer (`main.py`):** FastAPI application exposing clean, documented REST HTTP endpoints.
