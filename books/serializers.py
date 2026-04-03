from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Avg
from .models import (
    Genre,
    Author,
    Book,
    UserProfile,
    Rating,
    UserInteraction,
    RecommendationFeedback,
    ModelMetadata,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = ["date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "description"]


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio", "birth_date", "death_date"]


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    num_ratings = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "authors",
            "publisher",
            "publication_year",
            "genres",
            "description",
            "page_count",
            "language",
            "image_url_small",
            "image_url_medium",
            "image_url_large",
            "avg_rating",
            "num_ratings",
            "date_added",
        ]
        read_only_fields = ["date_added"]

    def get_avg_rating(self, obj):
        ratings = obj.ratings.all()
        if ratings.exists():
            return round(ratings.aggregate(Avg("rating"))["rating__avg"], 2)
        return None

    def get_num_ratings(self, obj):
        return obj.ratings.count()


class BookListSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    num_ratings = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "authors",
            "publication_year",
            "genres",
            "image_url_medium",
            "avg_rating",
            "num_ratings",
        ]

    def get_authors(self, obj):
        return [author.name for author in obj.authors.all()]

    def get_genres(self, obj):
        return [genre.name for genre in obj.genres.all()]

    def get_avg_rating(self, obj):
        ratings = obj.ratings.all()
        if ratings.exists():
            from django.db.models import Avg

            return round(ratings.aggregate(Avg("rating"))["rating__avg"], 2)
        return None

    def get_num_ratings(self, obj):
        return obj.ratings.count()


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    favorite_genres = GenreSerializer(many=True, read_only=True)
    favorite_authors = AuthorSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "bio",
            "date_of_birth",
            "favorite_genres",
            "favorite_authors",
            "preferred_languages",
            "email_notifications",
            "newsletter_subscription",
            "date_joined",
            "last_active",
        ]
        read_only_fields = ["date_joined", "last_active"]


class RatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    book_isbn = serializers.CharField(write_only=True)

    class Meta:
        model = Rating
        fields = [
            "id",
            "user",
            "book",
            "book_isbn",
            "rating",
            "review",
            "date_created",
            "date_updated",
        ]
        read_only_fields = ["date_created", "date_updated"]

    def create(self, validated_data):
        book_isbn = validated_data.pop("book_isbn")
        try:
            book = Book.objects.get(isbn=book_isbn)
        except Book.DoesNotExist:
            raise serializers.ValidationError({"book_isbn": "Book not found."})

        validated_data["book"] = book
        validated_data["user"] = self.context["request"].user

        # Update or create rating
        rating, created = Rating.objects.update_or_create(
            user=validated_data["user"],
            book=validated_data["book"],
            defaults={
                "rating": validated_data["rating"],
                "review": validated_data.get("review", ""),
            },
        )
        return rating


class UserInteractionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    book_isbn = serializers.CharField(write_only=True)

    class Meta:
        model = UserInteraction
        fields = [
            "id",
            "user",
            "book",
            "book_isbn",
            "interaction_type",
            "timestamp",
            "session_id",
        ]
        read_only_fields = ["timestamp"]

    def create(self, validated_data):
        book_isbn = validated_data.pop("book_isbn")
        try:
            book = Book.objects.get(isbn=book_isbn)
        except Book.DoesNotExist:
            raise serializers.ValidationError({"book_isbn": "Book not found."})

        validated_data["book"] = book
        validated_data["user"] = self.context["request"].user

        return UserInteraction.objects.create(**validated_data)


class RecommendationFeedbackSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    book_isbn = serializers.CharField(write_only=True)

    class Meta:
        model = RecommendationFeedback
        fields = [
            "id",
            "user",
            "book",
            "book_isbn",
            "was_helpful",
            "feedback_text",
            "timestamp",
        ]
        read_only_fields = ["timestamp"]

    def create(self, validated_data):
        book_isbn = validated_data.pop("book_isbn")
        try:
            book = Book.objects.get(isbn=book_isbn)
        except Book.DoesNotExist:
            raise serializers.ValidationError({"book_isbn": "Book not found."})

        validated_data["book"] = book
        validated_data["user"] = self.context["request"].user

        feedback, created = RecommendationFeedback.objects.update_or_create(
            user=validated_data["user"],
            book=validated_data["book"],
            defaults={
                "was_helpful": validated_data["was_helpful"],
                "feedback_text": validated_data.get("feedback_text", ""),
            },
        )
        return feedback


class ModelMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelMetadata
        fields = [
            "id",
            "name",
            "version",
            "model_type",
            "training_date",
            "training_data_size",
            "metrics",
            "is_active",
            "notes",
        ]
        read_only_fields = ["training_date"]
