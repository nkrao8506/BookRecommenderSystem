"""
Tests for the Book Recommender API endpoints.
Run with: python manage.py test books.tests
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from books.models import Book, Author, Genre, Rating, UserProfile


class APITestCase(TestCase):
    """Base test case with API client setup"""

    def setUp(self):
        self.client = APIClient()

        # Create test user
        self.test_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.user_profile = UserProfile.objects.create(user=self.test_user)

        # Create test book
        self.test_book = Book.objects.create(
            isbn="1234567890", title="Test Book", publication_year=2023, language="en"
        )

        # Create test author
        self.test_author = Author.objects.create(name="Test Author")
        self.test_book.authors.add(self.test_author)

        # Create test genre
        self.test_genre = Genre.objects.create(name="Fiction")
        self.test_book.genres.add(self.test_genre)


class HealthCheckTest(APITestCase):
    """Test health check endpoint"""

    def test_health_check(self):
        """Health check should return 200 with status info"""
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")
        self.assertIn("timestamp", response.data)
        self.assertIn("version", response.data)


class AuthenticationTest(APITestCase):
    """Test authentication endpoints"""

    def test_user_registration(self):
        """Should register a new user and return token"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "newpass123",
        }
        response = self.client.post("/api/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "newuser")

        # Verify user was created
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertTrue(UserProfile.objects.filter(user__username="newuser").exists())

    def test_user_registration_password_mismatch(self):
        """Should fail if passwords don't match"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "differentpass",
        }
        response = self.client.post("/api/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        """Should login user and return token"""
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post("/api/auth/login/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], "testuser")

    def test_user_login_invalid_credentials(self):
        """Should fail with invalid credentials"""
        data = {"username": "testuser", "password": "wrongpass"}
        response = self.client.post("/api/auth/login/", data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_logout(self):
        """Should logout user and delete token"""
        # Login first to get token
        self.client.post(
            "/api/auth/login/", {"username": "testuser", "password": "testpass123"}
        )

        # Get token
        from rest_framework.authtoken.models import Token

        token = Token.objects.get(user=self.test_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        # Logout
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify token was deleted
        self.assertFalse(Token.objects.filter(user=self.test_user).exists())


class BookAPITest(APITestCase):
    """Test book API endpoints"""

    def test_list_books(self):
        """Should return list of books"""
        response = self.client.get("/api/books/list/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreater(len(response.data["results"]), 0)

    def test_book_detail(self):
        """Should return book details"""
        response = self.client.get(f"/api/books/{self.test_book.isbn}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Book")
        self.assertEqual(response.data["isbn"], "1234567890")

    def test_book_search(self):
        """Should search books by title"""
        response = self.client.get("/api/books/list/", {"search": "Test Book"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

    def test_similar_books(self):
        """Should return similar books"""
        response = self.client.get(f"/api/books/{self.test_book.isbn}/similar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("book", response.data)
        self.assertIn("similar_books", response.data)


class RatingAPITest(APITestCase):
    """Test rating API endpoints"""

    def setUp(self):
        super().setUp()
        # Login to get token
        self.client.post(
            "/api/auth/login/", {"username": "testuser", "password": "testpass123"}
        )
        from rest_framework.authtoken.models import Token

        self.token = Token.objects.get(user=self.test_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_create_rating(self):
        """Should create a rating for a book"""
        data = {"book_isbn": self.test_book.isbn, "rating": 4, "review": "Great book!"}
        response = self.client.post("/api/ratings/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["rating"], 4)
        self.assertEqual(response.data["review"], "Great book!")

    def test_list_user_ratings(self):
        """Should list user's ratings"""
        # Create a rating first
        Rating.objects.create(
            user=self.test_user, book=self.test_book, rating=5, review="Excellent!"
        )

        response = self.client.get("/api/ratings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

    def test_create_rating_unauthenticated(self):
        """Should fail if not authenticated"""
        # Create a new unauthenticated client
        from rest_framework.test import APIClient

        unauth_client = APIClient()
        data = {"book_isbn": self.test_book.isbn, "rating": 4}
        response = unauth_client.post("/api/ratings/", data)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )


class RecommendationTest(APITestCase):
    """Test recommendation endpoints"""

    def setUp(self):
        super().setUp()
        # Login to get token
        self.client.post(
            "/api/auth/login/", {"username": "testuser", "password": "testpass123"}
        )
        from rest_framework.authtoken.models import Token

        self.token = Token.objects.get(user=self.test_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_recommendations_cold_start(self):
        """Should return popular books for new users"""
        response = self.client.get("/api/recommendations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("recommendations", response.data)
        self.assertIn("reason", response.data)
        self.assertEqual(response.data["reason"], "popular_books")

    def test_recommendations_with_ratings(self):
        """Should return personalized recommendations for users with ratings"""
        # Create some ratings
        book2 = Book.objects.create(
            isbn="0987654321", title="Another Book", publication_year=2022
        )
        book2.authors.add(self.test_author)
        book2.genres.add(self.test_genre)

        Rating.objects.create(user=self.test_user, book=self.test_book, rating=5)
        Rating.objects.create(user=self.test_user, book=book2, rating=4)

        response = self.client.get("/api/recommendations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("recommendations", response.data)


class DashboardTest(APITestCase):
    """Test dashboard endpoint"""

    def setUp(self):
        super().setUp()
        # Login to get token
        self.client.post(
            "/api/auth/login/", {"username": "testuser", "password": "testpass123"}
        )
        from rest_framework.authtoken.models import Token

        self.token = Token.objects.get(user=self.test_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_dashboard_stats(self):
        """Should return user dashboard statistics"""
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_ratings", response.data)
        self.assertIn("total_interactions", response.data)
        self.assertIn("average_rating", response.data)
        self.assertIn("favorite_genres", response.data)
        self.assertIn("recent_activity", response.data)
