import pandas as pd
from knowledge_base import KnowledgeBase, Book, Interaction


def _clean_cell(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text and text.lower() != "nan" else None


def _get_description(row):
    for column_name in ("Book-Description", "Description", "description", "Summary", "summary"):
        value = _clean_cell(row.get(column_name))
        if value:
            return value
    return None

def load_data():
    kb = KnowledgeBase()
    
    print("Loading books...")
    # Read just a subset of books to start
    try:
        books_df = pd.read_csv("Books.csv", dtype=str).head(100)
        for _, row in books_df.iterrows():
            book = Book(
                id=_clean_cell(row.get('ISBN')) or "",
                title=_clean_cell(row.get('Book-Title')) or "",
                authors=_clean_cell(row.get('Book-Author')) or "",
                year=_clean_cell(row.get('Year-Of-Publication')),
                publisher=_clean_cell(row.get('Publisher')),
                image_url=_clean_cell(row.get('Image-URL-L')) or _clean_cell(row.get('Image-URL-M')) or _clean_cell(row.get('Image-URL-S')),
                description=_get_description(row)
            )
            kb.add_book(book)
        print(f"Loaded {len(books_df)} books.")
    except Exception as e:
        print(f"Error loading books: {e}")

    print("Loading ratings...")
    try:
        ratings_df = pd.read_csv("Ratings.csv").head(500)
        for _, row in ratings_df.iterrows():
            kb.add_interaction(
                user_id=str(row['User-ID']),
                book_id=str(row['ISBN']),
                rating=float(row['Book-Rating'])
            )
        print(f"Loaded {len(ratings_df)} ratings.")
    except Exception as e:
        print(f"Error loading ratings: {e}")

if __name__ == "__main__":
    load_data()
