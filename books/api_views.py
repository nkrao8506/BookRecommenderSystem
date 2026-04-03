from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.utils import timezone
from .models import (
    Book,
    Rating,
    UserInteraction,
    RecommendationFeedback,
    ModelMetadata,
    Genre,
    Author,
    UserProfile,
)
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    BookSerializer,
    BookListSerializer,
    RatingSerializer,
    UserInteractionSerializer,
    RecommendationFeedbackSerializer,
    ModelMetadataSerializer,
    UserProfileSerializer,
    GenreSerializer,
    AuthorSerializer,
)
import numpy as np
import pickle
import os


# Authentication Views
class UserRegistrationView(generics.CreateAPIView):
    """Register a new user and return authentication token"""

    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create user profile
        UserProfile.objects.create(user=user)

        # Generate token
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
                "message": "User registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )


class UserLoginView(generics.GenericAPIView):
    """Login user and return authentication token"""

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)

            # Update last active (ensure profile exists)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.last_active = timezone.now()
            profile.save()

            return Response(
                {
                    "user": UserSerializer(user).data,
                    "token": token.key,
                    "message": "Login successful",
                }
            )
        else:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )


class UserLogoutView(generics.GenericAPIView):
    """Logout user and delete token"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response({"message": "Logout successful"})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


# Book Views
class BookListView(generics.ListAPIView):
    """List all books with search and filtering"""

    serializer_class = BookListSerializer
    permission_classes = [AllowAny]
    search_fields = ["title", "authors__name", "genres__name"]
    ordering_fields = ["title", "publication_year", "date_added"]
    ordering = ["title"]

    def get_queryset(self):
        queryset = Book.objects.all().prefetch_related("authors", "genres")

        # Filter by genre
        genre = self.request.query_params.get("genre", None)
        if genre:
            queryset = queryset.filter(genres__name__iexact=genre)

        # Filter by author
        author = self.request.query_params.get("author", None)
        if author:
            queryset = queryset.filter(authors__name__icontains=author)

        # Filter by year range
        year_min = self.request.query_params.get("year_min", None)
        year_max = self.request.query_params.get("year_max", None)
        if year_min:
            queryset = queryset.filter(publication_year__gte=year_min)
        if year_max:
            queryset = queryset.filter(publication_year__lte=year_max)

        # Filter by language
        language = self.request.query_params.get("language", None)
        if language:
            queryset = queryset.filter(language__iexact=language)

        return queryset


class BookDetailView(generics.RetrieveAPIView):
    """Get detailed information about a specific book"""

    queryset = Book.objects.all().prefetch_related("authors", "genres", "ratings")
    serializer_class = BookSerializer
    lookup_field = "isbn"
    permission_classes = [AllowAny]


class PopularBooksView(generics.ListAPIView):
    """Get most popular books based on ratings"""

    serializer_class = BookListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Book.objects.annotate(
                num_ratings=Count("ratings"), avg_rating=Avg("ratings__rating")
            )
            .filter(num_ratings__gt=0)
            .order_by("-num_ratings", "-avg_rating")[:50]
        )


# Rating Views
class RatingListCreateView(generics.ListCreateAPIView):
    """List user's ratings or create a new rating"""

    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user).select_related("book")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific rating"""

    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user)


# User Interaction Views
class UserInteractionCreateView(generics.CreateAPIView):
    """Track user interactions with books"""

    serializer_class = UserInteractionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserInteractionListView(generics.ListAPIView):
    """List user's interactions"""

    serializer_class = UserInteractionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserInteraction.objects.filter(user=self.request.user).select_related(
            "book"
        )


# Recommendation Views
class RecommendationView(generics.GenericAPIView):
    """Get personalized recommendations for the authenticated user"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get user's ratings
        user_ratings = Rating.objects.filter(user=user)

        if not user_ratings.exists():
            # Cold start: return popular books
            popular_books = (
                Book.objects.annotate(
                    num_ratings=Count("ratings"), avg_rating=Avg("ratings__rating")
                )
                .filter(num_ratings__gt=0)
                .order_by("-num_ratings", "-avg_rating")[:20]
            )

            serializer = BookListSerializer(popular_books, many=True)
            return Response(
                {
                    "recommendations": serializer.data,
                    "reason": "popular_books",
                    "message": "Rate some books to get personalized recommendations!",
                }
            )

        # Get books the user has rated
        rated_book_isbns = user_ratings.values_list("book_id", flat=True)

        # Simple collaborative filtering based on user's ratings
        # Find users with similar taste
        similar_users = (
            Rating.objects.filter(book_id__in=rated_book_isbns)
            .exclude(user=user)
            .values("user")
            .annotate(common_books=Count("book"))
            .filter(common_books__gt=2)
            .order_by("-common_books")[:10]
        )

        similar_user_ids = [su["user"] for su in similar_users]

        # Get books rated by similar users that the current user hasn't rated
        recommendations = (
            Book.objects.filter(ratings__user_id__in=similar_user_ids)
            .exclude(isbn__in=rated_book_isbns)
            .annotate(num_ratings=Count("ratings"), avg_rating=Avg("ratings__rating"))
            .distinct()
            .order_by("-avg_rating", "-num_ratings")[:20]
        )

        serializer = BookListSerializer(recommendations, many=True)
        return Response(
            {"recommendations": serializer.data, "reason": "collaborative_filtering"}
        )


class SimilarBooksView(generics.RetrieveAPIView):
    """Get books similar to a specific book"""

    queryset = Book.objects.all()
    serializer_class = BookListSerializer
    lookup_field = "isbn"
    permission_classes = [AllowAny]

    def retrieve(self, request, isbn=None):
        book = self.get_object()

        # Simple content-based similarity based on genres and authors
        similar_books = (
            Book.objects.filter(
                Q(genres__in=book.genres.all()) | Q(authors__in=book.authors.all())
            )
            .exclude(isbn=book.isbn)
            .distinct()
            .annotate(num_ratings=Count("ratings"), avg_rating=Avg("ratings__rating"))
            .order_by("-avg_rating", "-num_ratings")[:10]
        )

        serializer = BookListSerializer(similar_books, many=True)
        return Response(
            {"book": BookSerializer(book).data, "similar_books": serializer.data}
        )


# Feedback Views
class RecommendationFeedbackView(generics.CreateAPIView):
    """Submit feedback on recommendations"""

    serializer_class = RecommendationFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Admin/Metadata Views
class ModelMetadataView(generics.ListAPIView):
    """List model metadata (admin only)"""

    serializer_class = ModelMetadataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ModelMetadata.objects.all().order_by("-training_date")


# Health Check
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    return Response(
        {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
        }
    )


# Dashboard Stats
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for the user"""
    user = request.user

    user_ratings = Rating.objects.filter(user=user)
    user_interactions = UserInteraction.objects.filter(user=user)

    # Get user's favorite genres
    favorite_genres = (
        Genre.objects.filter(books__ratings__user=user)
        .annotate(rating_count=Count("books__ratings"))
        .order_by("-rating_count")[:5]
    )

    # Get user's reading activity
    recent_activity = user_interactions.order_by("-timestamp")[:10]

    return Response(
        {
            "total_ratings": user_ratings.count(),
            "total_interactions": user_interactions.count(),
            "average_rating": user_ratings.aggregate(Avg("rating"))["rating__avg"] or 0,
            "favorite_genres": GenreSerializer(favorite_genres, many=True).data,
            "recent_activity": UserInteractionSerializer(
                recent_activity, many=True
            ).data,
        }
    )
