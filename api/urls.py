from django.urls import path
from .index import (
    CategoryListAPIView,
    EventDetailAPIView,
    EventListAPIView,
    RegistrationListCreateAPIView,
)

urlpatterns = [
    path("events/", EventListAPIView.as_view(), name="api_event_list"),
    path("events/<int:pk>/", EventDetailAPIView.as_view(), name="api_event_detail"),
    path("registrations/", RegistrationListCreateAPIView.as_view(), name="api_registrations"),
    path("categories/", CategoryListAPIView.as_view(), name="api_categories"),
]
