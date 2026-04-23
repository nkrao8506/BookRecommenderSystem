import os
import pickle
import numpy as np
import base64
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

popular_df = None
pt = None
books = None
similarity_score = None


def load_models():
    global popular_df, pt, books, similarity_score
    if popular_df is None:
        try:
            popular_df = pickle.load(open(os.path.join(BASE_DIR, "popular.pkl"), "rb"))
            pt = pickle.load(open(os.path.join(BASE_DIR, "pt.pkl"), "rb"))
            books = pickle.load(open(os.path.join(BASE_DIR, "books.pkl"), "rb"))
            similarity_score = pickle.load(
                open(os.path.join(BASE_DIR, "similarity_score.pkl"), "rb")
            )
        except Exception as e:
            print(f"Error loading models: {e}")
            popular_df, pt, books, similarity_score = None, None, None, None
    return popular_df, pt, books, similarity_score

# Load models at application startup
load_models()


def index(request):
    popular_df, _, _, _ = load_models()

    books_data = []
    for i in range(len(popular_df)):
        books_data.append(
            {
                "title": popular_df.iloc[i]["Book-Title"],
                "author": popular_df.iloc[i]["Book-Author"],
                "image": popular_df.iloc[i]["Image-URL-M"],
                "votes": int(popular_df.iloc[i]["num_ratings"]),
                "rating": round(float(popular_df.iloc[i]["avg_rating"]), 1),
            }
        )

    return JsonResponse({"books": books_data})


@csrf_exempt
@require_http_methods(["POST"])
def recommend_books(request):
    popular_df, pt, books_df, similarity_score = load_models()

    import json

    try:
        data = json.loads(request.body)
        user_input = data.get("book_title", "")
    except:
        user_input = request.POST.get("user_input", "")

    if not user_input:
        return JsonResponse({"error": "No book title provided"}, status=400)

    try:
        index = np.where(pt.index == user_input)[0][0]
    except IndexError:
        return JsonResponse({"error": "Book not found"}, status=404)

    similar_items = sorted(
        list(enumerate(similarity_score[index])), key=lambda x: x[1], reverse=True
    )[1:6]

    recommendations = []
    for i in similar_items:
        temp_df = books_df[books_df["Book-Title"] == pt.index[i[0]]]
        if not temp_df.empty:
            recommendations.append(
                {
                    "title": temp_df.iloc[0]["Book-Title"],
                    "author": temp_df.iloc[0]["Book-Author"],
                    "image": temp_df.iloc[0]["Image-URL-M"],
                }
            )

    return JsonResponse({"recommendations": recommendations})


def get_book_list(request):
    _, pt, _, _ = load_models()
    book_titles = pt.index.tolist()
    return JsonResponse({"books": book_titles})


@csrf_exempt
@require_http_methods(["POST"])
def upload_book(request):
    popular_df, pt, books_df, similarity_score = load_models()

    import json
    import re

    try:
        content_type = request.content_type
        if "multipart/form-data" in content_type:
            book_title = request.POST.get("book_name", "")
            rating = request.POST.get("rating", "0")
            review = request.POST.get("review", "")
            image = request.FILES.get("image")
        else:
            data = json.loads(request.body)
            book_title = data.get("book_name", "")
            rating = data.get("rating", "0")
            review = data.get("review", "")
            image_data = data.get("image", "")
    except Exception as e:
        return JsonResponse({"error": f"Invalid request: {str(e)}"}, status=400)

    if not book_title:
        return JsonResponse({"error": "Book name is required"}, status=400)

    uploaded_book_image = None

    if image:
        ext = image.name.split(".")[-1] if "." in image.name else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        upload_dir = os.path.join(BASE_DIR, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            for chunk in image.chunks():
                f.write(chunk)
        uploaded_book_image = f"/uploads/{filename}"

    user_rating = float(rating) if rating else 0

    recommendations = []
    error_message = None

    try:
        matching_books = books_df[
            books_df["Book-Title"].str.lower() == book_title.lower()
        ]

        if matching_books.empty:
            words = book_title.lower().split()
            for word in words:
                if len(word) > 3:
                    matching_books = books_df[
                        books_df["Book-Title"].str.lower().str.contains(word, na=False)
                    ]
                    if not matching_books.empty:
                        break

        if not matching_books.empty:
            matched_title = matching_books.iloc[0]["Book-Title"]
            index = np.where(pt.index == matched_title)[0]

            if len(index) > 0:
                index = index[0]
                similar_items = sorted(
                    list(enumerate(similarity_score[index])),
                    key=lambda x: x[1],
                    reverse=True,
                )[1:6]

                for i in similar_items:
                    temp_df = books_df[books_df["Book-Title"] == pt.index[i[0]]]
                    if not temp_df.empty:
                        recommendations.append(
                            {
                                "title": temp_df.iloc[0]["Book-Title"],
                                "author": temp_df.iloc[0]["Book-Author"],
                                "image": temp_df.iloc[0]["Image-URL-M"],
                                "match_score": round(float(i[1]) * 100, 1),
                            }
                        )
        else:
            error_message = f"Book '{book_title}' not found in database. Try a more common book title for better recommendations."

    except Exception as e:
        error_message = f"Error generating recommendations: {str(e)}"

    result = {
        "uploaded_book": {
            "title": book_title,
            "rating": user_rating,
            "review": review,
            "image": uploaded_book_image if uploaded_book_image else None,
        },
        "recommendations": recommendations,
    }

    if error_message:
        result["error"] = error_message

    return JsonResponse(result)
