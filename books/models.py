from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=200, unique=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(blank=True, null=True)
    death_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    isbn = models.CharField(max_length=13, primary_key=True)
    title = models.CharField(max_length=500)
    authors = models.ManyToManyField(Author, related_name="books")
    publisher = models.CharField(max_length=200, blank=True, null=True)
    publication_year = models.IntegerField(blank=True, null=True)
    genres = models.ManyToManyField(Genre, related_name="books", blank=True)
    description = models.TextField(blank=True)
    page_count = models.IntegerField(blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, default="en")
    isbn_13 = models.CharField(max_length=13, blank=True, null=True)
    lccn = models.CharField(max_length=20, blank=True, null=True)
    oclc_number = models.CharField(max_length=20, blank=True, null=True)
    subjects = models.TextField(blank=True)  # Additional subjects/categories

    # Image URLs
    image_url_small = models.URLField(blank=True, null=True)
    image_url_medium = models.URLField(blank=True, null=True)
    image_url_large = models.URLField(blank=True, null=True)

    # Metadata
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["publication_year"]),
        ]

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    favorite_genres = models.ManyToManyField(
        Genre, related_name="user_profiles", blank=True
    )
    favorite_authors = models.ManyToManyField(
        Author, related_name="user_profiles", blank=True
    )
    preferred_languages = models.CharField(
        max_length=100, blank=True, default="en"
    )  # Comma-separated
    email_notifications = models.BooleanField(default=True)
    newsletter_subscription = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="ratings")
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)], help_text="Rating from 1 to 5"
    )
    review = models.TextField(blank=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "book")
        indexes = [
            models.Index(fields=["user", "book"]),
            models.Index(fields=["date_created"]),
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.book.title}: {self.rating}/5"


class UserInteraction(models.Model):
    INTERACTION_TYPES = [
        ("view", "Viewed Book"),
        ("click", "Clicked Recommendation"),
        ("wishlist", "Added to Wishlist"),
        ("cart", "Added to Cart"),
        ("purchase", "Purchased"),
        ("share", "Shared"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="interactions"
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="interactions"
    )
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["book", "timestamp"]),
            models.Index(fields=["interaction_type", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.book.title}"


class RecommendationFeedback(models.Model):
    """Store explicit feedback on recommendations for improving the algorithm"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recommendation_feedback"
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="recommendation_feedback"
    )
    was_helpful = models.BooleanField()  # Thumbs up/down
    feedback_text = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "book")
        indexes = [
            models.Index(fields=["user", "timestamp"]),
        ]

    def __str__(self):
        return f"Feedback from {self.user.username} on {self.book.title}: {'Helpful' if self.was_helpful else 'Not Helpful'}"


class ModelMetadata(models.Model):
    """Track ML model versions and performance metrics"""

    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    model_type = models.CharField(
        max_length=50
    )  # e.g., 'collaborative_filtering', 'content_based', 'hybrid'
    training_date = models.DateTimeField(default=timezone.now)
    training_data_size = models.IntegerField(
        help_text="Number of ratings used for training"
    )
    metrics = models.JSONField(
        default=dict, blank=True
    )  # Store metrics like precision, recall, etc.
    is_active = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-training_date"]
        indexes = [
            models.Index(fields=["name", "version"]),
            models.Index(fields=["is_active", "-training_date"]),
        ]

    def __str__(self):
        return (
            f"{self.name} v{self.version} ({self.training_date.strftime('%Y-%m-%d')})"
        )
