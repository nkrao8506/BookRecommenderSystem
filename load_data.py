import pandas as pd
from knowledge_base import KnowledgeBase, Book, Interaction

def load_data():
    kb = KnowledgeBase()
    
    print("Loading books...")
    # Read just a subset of books to start
    try:
        books_df = pd.read_csv("Books.csv", dtype=str).head(100)
        for _, row in books_df.iterrows():
            book = Book(
                id=str(row.get('ISBN', '')),
                title=str(row.get('Book-Title', '')),
                authors=str(row.get('Book-Author', '')),
                year=str(row.get('Year-Of-Publication', '')),
                publisher=str(row.get('Publisher', '')),
                image_url=str(row.get('Image-URL-L', ''))
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
