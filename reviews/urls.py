from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("event/<int:event_pk>/submit/", views.submit_review, name="submit_review"),
    path("<int:review_pk>/delete/", views.delete_review, name="delete_review"),
]
