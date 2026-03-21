from django.urls import path

from . import views

app_name = "comments"

urlpatterns = [
    path("event/<int:event_pk>/add/", views.add_comment, name="add_comment"),
    path("<int:comment_pk>/delete/", views.delete_comment, name="delete_comment"),
]
