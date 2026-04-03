from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
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


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["name", "birth_date", "death_date"]
    search_fields = ["name"]
    list_filter = ["birth_date"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "publication_year", "language", "date_added"]
    search_fields = ["title", "authors__name"]
    list_filter = ["publication_year", "language", "genres"]
    filter_horizontal = ["authors", "genres"]
    date_hierarchy = "date_added"


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["user", "book", "rating", "date_created"]
    search_fields = ["user__username", "book__title"]
    list_filter = ["rating", "date_created"]
    date_hierarchy = "date_created"


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ["user", "book", "interaction_type", "timestamp"]
    search_fields = ["user__username", "book__title"]
    list_filter = ["interaction_type", "timestamp"]
    date_hierarchy = "timestamp"


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(admin.ModelAdmin):
    list_display = ["user", "book", "was_helpful", "timestamp"]
    search_fields = ["user__username", "book__title"]
    list_filter = ["was_helpful", "timestamp"]
    date_hierarchy = "timestamp"


@admin.register(ModelMetadata)
class ModelMetadataAdmin(admin.ModelAdmin):
    list_display = ["name", "version", "model_type", "training_date", "is_active"]
    search_fields = ["name", "version"]
    list_filter = ["model_type", "is_active", "training_date"]
    date_hierarchy = "training_date"
