from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # Authentication endpoints
    path(
        "auth/register/",
        api_views.UserRegistrationView.as_view(),
        name="api-register",
    ),
    path("auth/login/", api_views.UserLoginView.as_view(), name="api-login"),
    path("auth/logout/", api_views.UserLogoutView.as_view(), name="api-logout"),
    path("auth/profile/", api_views.UserProfileView.as_view(), name="api-profile"),
    # Book endpoints (before legacy endpoints to avoid conflicts)
    path("books/list/", api_views.BookListView.as_view(), name="api-books"),
    path(
        "books/popular/",
        api_views.PopularBooksView.as_view(),
        name="api-popular-books",
    ),
    path(
        "books/<str:isbn>/",
        api_views.BookDetailView.as_view(),
        name="api-book-detail",
    ),
    path(
        "books/<str:isbn>/similar/",
        api_views.SimilarBooksView.as_view(),
        name="api-similar-books",
    ),
    # Rating endpoints
    path("ratings/", api_views.RatingListCreateView.as_view(), name="api-ratings"),
    path(
        "ratings/<int:pk>/",
        api_views.RatingDetailView.as_view(),
        name="api-rating-detail",
    ),
    # User interaction endpoints
    path(
        "interactions/",
        api_views.UserInteractionListView.as_view(),
        name="api-interactions",
    ),
    path(
        "interactions/create/",
        api_views.UserInteractionCreateView.as_view(),
        name="api-interaction-create",
    ),
    # Recommendation endpoints
    path(
        "recommendations/",
        api_views.RecommendationView.as_view(),
        name="api-recommendations",
    ),
    # Feedback endpoints
    path(
        "feedback/",
        api_views.RecommendationFeedbackView.as_view(),
        name="api-feedback",
    ),
    # Admin/Metadata endpoints
    path("models/", api_views.ModelMetadataView.as_view(), name="api-models"),
    # Health and dashboard
    path("health/", api_views.health_check, name="api-health"),
    path("dashboard/", api_views.dashboard_stats, name="api-dashboard"),
    # Legacy Flask-compatible endpoints (at the end to avoid conflicts)
    path("", views.index, name="index"),
    path("recommend/", views.recommend_books, name="recommend_books"),
    path("books/", views.get_book_list, name="book_list"),
    path("upload/", views.upload_book, name="upload_book"),
]
