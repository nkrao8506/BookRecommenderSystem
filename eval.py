"""
Offline evaluation: Precision@k, Recall@k, and NDCG@k for the recommender's
RETRIEVAL step, comparing FAISS semantic search against the random-sampling
baseline it replaced.

This deliberately evaluates retrieval only, not the LLM's reranking on top
of it. Retrieval quality (does the right book even make it into the
candidate pool?) is a separate question from how well the LLM ranks or
explains whatever it's handed - and isolating retrieval means this script
needs zero LLM calls, so it's cheap to rerun after any change.

Method: leave-one-out holdout, standard for implicit-feedback recommender
evaluation. For each user with at least MIN_LIKED_BOOKS liked books
(rating >= LIKED_RATING_THRESHOLD, matching LLMRecommender's own threshold)
that exist in the catalog:
    1. Hold out one liked book as the "target".
    2. Build a query from the user's remaining liked books (their "history").
    3. Retrieve the top-k candidates two ways: FAISS semantic search, and
       the old random-sampling baseline.
    4. Check whether the target appears in each candidate set, and at what
       rank.

With exactly one relevant (held-out) item per case:
    Precision@k = 1/k if found in the top-k, else 0
    Recall@k    = 1   if found in the top-k, else 0
    NDCG@k      = 1 / log2(rank + 2) if found, else 0   (rank is 0-indexed)

Usage:
    python eval.py [--k 10] [--random-trials 5] [--seed 42]
"""
import argparse
import math
import random

from embeddings import book_text_for_embedding, embed_query, get_embedding_dim
from knowledge_base import KnowledgeBase
from vector_store import VectorStore

# Matches LLMRecommender.LIKED_RATING_THRESHOLD / CANDIDATE_POOL_SIZE - kept
# as separate constants here so eval.py has no import-time dependency on
# recommender.py (which would require an LLM client to even construct).
LIKED_RATING_THRESHOLD = 7
MIN_LIKED_BOOKS = 2  # need >=1 to hold out and >=1 left as history context


def build_holdout_set(kb: KnowledgeBase) -> list[dict]:
    """
    Returns one holdout case per eligible user:
        {"user_id": ..., "history_ids": [...], "target_id": ...}

    Only interactions whose book_id actually exists in the catalog are used.
    Note: with the small demo dataset load_data.py loads by default (first
    100 books, first 500 ratings - independently sliced, so most rated ISBNs
    fall outside the 100-book sample), very few or zero users may qualify.
    That's a data-volume artifact of the demo sample, not a bug in this
    script - load more rows in load_data.py for a meaningful sample size.
    """
    catalog_ids = {b.id for b in kb.get_all_books()}

    holdout_cases = []
    for user_id in kb.get_all_user_ids():
        profile = kb.get_user_profile(user_id)
        liked_ids = [
            i.book_id for i in profile.interactions
            if i.rating >= LIKED_RATING_THRESHOLD and i.book_id in catalog_ids
        ]
        liked_ids = list(dict.fromkeys(liked_ids))  # de-dupe, preserve order
        if len(liked_ids) < MIN_LIKED_BOOKS:
            continue

        holdout_cases.append({
            "user_id": user_id,
            "history_ids": liked_ids[:-1],  # kept as known history/context
            "target_id": liked_ids[-1],     # held out - this is what we try to retrieve
        })
    return holdout_cases


def semantic_topk(kb: KnowledgeBase, store: VectorStore, history_ids: list[str], k: int) -> list[str]:
    """Same query-construction logic as LLMRecommender.recommend_for_user:
    concatenate the user's liked books' text, embed it, search the index."""
    history_books = kb.get_books_by_ids(history_ids)
    profile_text = " | ".join(
        book_text_for_embedding(b.title, b.authors, b.description, b.genres)
        for b in history_books
    )
    query_vector = embed_query(profile_text)
    hits = store.search(query_vector, k=k, exclude_ids=set(history_ids))
    return [book_id for book_id, _score in hits]


def random_topk(all_book_ids: list[str], k: int, exclude_ids: set[str], rng: random.Random) -> list[str]:
    """Mirrors the old kb.search_books(limit=k) behavior (ORDER BY RANDOM()),
    seeded for reproducibility. exclude_ids matches what the semantic search
    excludes, so the comparison stays apples-to-apples."""
    candidates = [bid for bid in all_book_ids if bid not in exclude_ids]
    rng.shuffle(candidates)
    return candidates[:k]


def precision_at_k(hit_rank: int | None, k: int) -> float:
    return (1.0 / k) if (hit_rank is not None and hit_rank < k) else 0.0


def recall_at_k(hit_rank: int | None, k: int) -> float:
    return 1.0 if (hit_rank is not None and hit_rank < k) else 0.0


def ndcg_at_k(hit_rank: int | None, k: int) -> float:
    if hit_rank is None or hit_rank >= k:
        return 0.0
    return 1.0 / math.log2(hit_rank + 2)  # IDCG = 1 for a single relevant item


def _score_case(retrieved_ids: list[str], target_id: str, k: int) -> tuple[float, float, float]:
    rank = retrieved_ids.index(target_id) if target_id in retrieved_ids else None
    return precision_at_k(rank, k), recall_at_k(rank, k), ndcg_at_k(rank, k)


def evaluate(kb: KnowledgeBase, store: VectorStore, holdout_cases: list[dict],
             k: int, random_trials: int, seed: int) -> dict:
    rng = random.Random(seed)
    all_book_ids = [b.id for b in kb.get_all_books()]

    semantic_scores = {"precision": [], "recall": [], "ndcg": []}
    random_scores = {"precision": [], "recall": [], "ndcg": []}

    for case in holdout_cases:
        target = case["target_id"]
        history = case["history_ids"]

        sem_ids = semantic_topk(kb, store, history, k)
        p, r, n = _score_case(sem_ids, target, k)
        semantic_scores["precision"].append(p)
        semantic_scores["recall"].append(r)
        semantic_scores["ndcg"].append(n)

        # Average over several random trials per case to smooth out luck.
        trial_p, trial_r, trial_n = [], [], []
        for _ in range(random_trials):
            rand_ids = random_topk(all_book_ids, k, exclude_ids=set(history), rng=rng)
            p, r, n = _score_case(rand_ids, target, k)
            trial_p.append(p)
            trial_r.append(r)
            trial_n.append(n)
        random_scores["precision"].append(sum(trial_p) / random_trials)
        random_scores["recall"].append(sum(trial_r) / random_trials)
        random_scores["ndcg"].append(sum(trial_n) / random_trials)

    def avg(xs):
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "semantic": {m: avg(v) for m, v in semantic_scores.items()},
        "random": {m: avg(v) for m, v in random_scores.items()},
    }


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval quality: FAISS semantic search vs. random baseline."
    )
    parser.add_argument("--k", type=int, default=10, help="Cutoff for Precision@k / Recall@k / NDCG@k")
    parser.add_argument("--random-trials", type=int, default=5,
                         help="Repeats per case for the random baseline, averaged to reduce noise")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    kb = KnowledgeBase()
    store = VectorStore(dim=get_embedding_dim())

    if store.is_empty():
        print("Vector store is empty. Run `python build_index.py` first.")
        return

    holdout_cases = build_holdout_set(kb)
    print(
        f"Built {len(holdout_cases)} holdout cases "
        f"(users with >= {MIN_LIKED_BOOKS} liked books in the catalog, rating >= {LIKED_RATING_THRESHOLD})."
    )

    if not holdout_cases:
        print(
            "\nNo eligible users found. With the default demo data (load_data.py's first 100 "
            "books and first 500 ratings, sliced independently), very few rated ISBNs land inside "
            "the 100-book sample. Increase the .head(N) limits in load_data.py, rerun load_data.py "
            "and build_index.py, then try again."
        )
        return

    results = evaluate(kb, store, holdout_cases, k=args.k, random_trials=args.random_trials, seed=args.seed)

    print(f"\n=== Retrieval evaluation @k={args.k} ({len(holdout_cases)} holdout users, "
          f"{args.random_trials} random trials/case) ===\n")
    header = f"{'Metric':<12}{'FAISS (semantic)':<20}{'Random baseline':<20}{'Lift':<10}"
    print(header)
    print("-" * len(header))
    for metric in ("precision", "recall", "ndcg"):
        sem = results["semantic"][metric]
        rand = results["random"][metric]
        print(f"{metric.capitalize():<12}{sem:<20.4f}{rand:<20.4f}{sem - rand:+.4f}")


if __name__ == "__main__":
    main()