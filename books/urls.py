from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("recommend/", views.recommend_books, name="recommend_books"),
    path("books/", views.get_book_list, name="book_list"),
    path("upload/", views.upload_book, name="upload_book"),
]
