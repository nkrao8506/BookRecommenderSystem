from django.db import models


class Book(models.Model):
    isbn = models.CharField(max_length=13, primary_key=True)
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    class Meta:
        app_label = "books"

    def __str__(self):
        return self.title
