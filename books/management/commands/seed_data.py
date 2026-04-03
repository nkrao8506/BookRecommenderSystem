"""
Management command to seed the database with data from CSV files.
Usage: python manage.py seed_data
"""

import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection
from books.models import Book, Author, Genre, Rating, UserProfile


class Command(BaseCommand):
    help = "Seed the database with data from CSV files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--books-csv", default="Books.csv", help="Path to Books.csv file"
        )
        parser.add_argument(
            "--ratings-csv", default="Ratings.csv", help="Path to Ratings.csv file"
        )
        parser.add_argument(
            "--users-csv", default="Users.csv", help="Path to Users.csv file"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of books to import (for testing)",
        )
        parser.add_argument(
            "--ratings-limit",
            type=int,
            default=None,
            help="Limit number of ratings to import (for testing)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Batch size for bulk inserts (default: 500)",
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting data seeding...")

        # Seed books
        books_csv = options["books_csv"]
        if os.path.exists(books_csv):
            self.seed_books(books_csv, options["limit"], options["batch_size"])
        else:
            self.stdout.write(self.style.WARNING(f"Books CSV not found at {books_csv}"))

        # Seed ratings
        ratings_csv = options["ratings_csv"]
        if os.path.exists(ratings_csv):
            self.seed_ratings(
                ratings_csv, options["ratings_limit"], options["batch_size"]
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Ratings CSV not found at {ratings_csv}")
            )

        self.stdout.write(self.style.SUCCESS("Data seeding completed!"))

    def seed_books(self, csv_path, limit=None, batch_size=500):
        self.stdout.write(f"Seeding books from {csv_path}...")

        books_created = 0
        authors_created = 0
        author_cache = {}
        book_cache = {}

        # Pre-load existing authors and books into cache
        for author in Author.objects.all():
            author_cache[author.name] = author
        for book in Book.objects.all():
            book_cache[book.isbn] = book

        books_to_create = []
        author_book_relations = []  # (book_isbn, author_name)

        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break

                isbn = row.get("ISBN", "").strip()
                title = row.get("Book-Title", "").strip()
                author = row.get("Book-Author", "").strip()
                year = row.get("Year-Of-Publication", "").strip()
                publisher = row.get("Publisher", "").strip()
                image_url_s = row.get("Image-URL-S", "").strip()
                image_url_m = row.get("Image-URL-M", "").strip()
                image_url_l = row.get("Image-URL-L", "").strip()

                if not isbn or not title:
                    continue

                # Skip if already in cache
                if isbn in book_cache:
                    if author:
                        author_book_relations.append((isbn, author[:200]))
                    continue

                books_to_create.append(
                    Book(
                        isbn=isbn,
                        title=title[:500],
                        publisher=publisher[:200] if publisher else None,
                        publication_year=int(year) if year and year.isdigit() else None,
                        image_url_small=image_url_s if image_url_s else None,
                        image_url_medium=image_url_m if image_url_m else None,
                        image_url_large=image_url_l if image_url_l else None,
                    )
                )
                book_cache[isbn] = True  # Mark as seen

                if author:
                    author_book_relations.append((isbn, author[:200]))

                # Bulk insert in batches
                if len(books_to_create) >= batch_size:
                    Book.objects.bulk_create(books_to_create, ignore_conflicts=True)
                    books_created += len(books_to_create)
                    books_to_create = []

                if (i + 1) % 1000 == 0:
                    self.stdout.write(f"  Processed {i + 1} books...")

        # Insert remaining books
        if books_to_create:
            Book.objects.bulk_create(books_to_create, ignore_conflicts=True)
            books_created += len(books_to_create)

        # Process authors
        authors_to_create = []
        seen_authors = set(author_cache.keys())

        for isbn, author_name in author_book_relations:
            if author_name not in author_cache and author_name not in seen_authors:
                authors_to_create.append(Author(name=author_name))
                seen_authors.add(author_name)

            if len(authors_to_create) >= batch_size:
                Author.objects.bulk_create(authors_to_create, ignore_conflicts=True)
                authors_created += len(authors_to_create)
                # Update cache
                for author in Author.objects.filter(
                    name__in=[a.name for a in authors_to_create]
                ):
                    author_cache[author.name] = author
                authors_to_create = []

        if authors_to_create:
            Author.objects.bulk_create(authors_to_create, ignore_conflicts=True)
            authors_created += len(authors_to_create)
            # Update cache
            for author in Author.objects.filter(
                name__in=[a.name for a in authors_to_create]
            ):
                author_cache[author.name] = author

        # Create book-author relationships
        self.stdout.write("  Creating book-author relationships...")
        relations_created = 0

        # Get all books and authors in batches to avoid SQL variable limits
        all_isbns = list(set(r[0] for r in author_book_relations))
        all_author_names = list(set(r[1] for r in author_book_relations))

        all_books = {}
        for i in range(0, len(all_isbns), batch_size):
            batch_isbns = all_isbns[i : i + batch_size]
            for b in Book.objects.filter(isbn__in=batch_isbns):
                all_books[b.isbn] = b

        all_authors = {}
        for i in range(0, len(all_author_names), batch_size):
            batch_names = all_author_names[i : i + batch_size]
            for a in Author.objects.filter(name__in=batch_names):
                all_authors[a.name] = a

        through_model = Book.authors.through
        relations_to_create = []
        seen_relations = set()

        for isbn, author_name in author_book_relations:
            if isbn in all_books and author_name in all_authors:
                book = all_books[isbn]
                author = all_authors[author_name]
                relation_key = (book.isbn, author.id)

                if relation_key not in seen_relations:
                    relations_to_create.append(
                        through_model(book_id=book.isbn, author_id=author.id)
                    )
                    seen_relations.add(relation_key)

                if len(relations_to_create) >= batch_size:
                    through_model.objects.bulk_create(
                        relations_to_create, ignore_conflicts=True
                    )
                    relations_created += len(relations_to_create)
                    relations_to_create = []

        if relations_to_create:
            through_model.objects.bulk_create(
                relations_to_create, ignore_conflicts=True
            )
            relations_created += len(relations_to_create)

        self.stdout.write(
            self.style.SUCCESS(
                f"  Books: {books_created} created, Authors: {authors_created} created, Relations: {relations_created}"
            )
        )

    def seed_ratings(self, csv_path, limit=None, batch_size=500):
        self.stdout.write(f"Seeding ratings from {csv_path}...")

        ratings_created = 0
        users_created = 0

        # Get or create a default admin user
        admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"email": "admin@example.com"}
        )
        admin_user.set_password("admin123")
        admin_user.save()
        UserProfile.objects.get_or_create(user=admin_user)

        # Pre-load existing books into cache (only ISBNs, not full objects)
        book_isbns = set(Book.objects.values_list("isbn", flat=True))
        user_cache = {}

        # Pre-load existing users
        for user in User.objects.filter(username__startswith="user_"):
            user_cache[user.username] = user

        ratings_to_create = []
        users_to_create = []
        seen_usernames = set(user_cache.keys())

        # Track which (user_id, isbn) pairs we've already seen to avoid duplicates
        seen_ratings = set()

        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break

                user_id = row.get("User-ID", "").strip()
                isbn = row.get("ISBN", "").strip()
                rating = row.get("Book-Rating", "").strip()

                if not user_id or not isbn or not rating:
                    continue

                try:
                    rating_value = int(rating)
                    if rating_value == 0:  # Skip implicit ratings
                        continue
                    if rating_value < 1 or rating_value > 10:
                        continue
                    # Normalize 1-10 scale to 1-5
                    rating_value = max(1, min(5, rating_value // 2))
                except ValueError:
                    continue

                # Skip if book doesn't exist
                if isbn not in book_isbns:
                    continue

                username = f"user_{user_id}"
                rating_key = (username, isbn)

                # Skip duplicate ratings
                if rating_key in seen_ratings:
                    continue
                seen_ratings.add(rating_key)

                # Create user if needed
                if username not in user_cache and username not in seen_usernames:
                    users_to_create.append(
                        User(username=username, email=f"{username}@example.com")
                    )
                    seen_usernames.add(username)

                if len(users_to_create) >= batch_size:
                    User.objects.bulk_create(users_to_create)
                    users_created += len(users_to_create)
                    # Reload users from DB and set passwords
                    for u in users_to_create:
                        try:
                            user = User.objects.get(username=u.username)
                            user.set_password("password123")
                            user.save(update_fields=["password"])
                            UserProfile.objects.get_or_create(user=user)
                            user_cache[user.username] = user
                        except User.DoesNotExist:
                            pass  # User already existed
                    users_to_create = []

                # Get user and book
                if username in user_cache:
                    user = user_cache[username]
                else:
                    try:
                        user = User.objects.get(username=username)
                        user_cache[username] = user
                    except User.DoesNotExist:
                        continue  # Skip if user wasn't created

                ratings_to_create.append(
                    Rating(
                        user=user,
                        book_id=isbn,  # Use book_id directly since isbn is the primary key
                        rating=rating_value,
                    )
                )

                if len(ratings_to_create) >= batch_size:
                    # Use bulk_create with ignore_conflicts for unique constraint
                    Rating.objects.bulk_create(
                        ratings_to_create,
                        ignore_conflicts=True,
                        unique_fields=["user", "book"],
                    )
                    ratings_created += len(ratings_to_create)
                    ratings_to_create = []

                if (i + 1) % 10000 == 0:
                    self.stdout.write(f"  Processed {i + 1} ratings...")

        # Insert remaining users
        if users_to_create:
            User.objects.bulk_create(users_to_create)
            users_created += len(users_to_create)
            for u in users_to_create:
                try:
                    user = User.objects.get(username=u.username)
                    user.set_password("password123")
                    user.save(update_fields=["password"])
                    UserProfile.objects.get_or_create(user=user)
                    user_cache[user.username] = user
                except User.DoesNotExist:
                    pass

        # Insert remaining ratings
        if ratings_to_create:
            Rating.objects.bulk_create(
                ratings_to_create, ignore_conflicts=True, unique_fields=["user", "book"]
            )
            ratings_created += len(ratings_to_create)

        self.stdout.write(
            self.style.SUCCESS(
                f"  Ratings: {ratings_created} created, Users: {users_created} created"
            )
        )
