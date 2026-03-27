from django.urls import path
from .views import ChatView

app_name = 'chatbot'

urlpatterns = [
    path('ask/', ChatView.as_view(), name='ask'),
]
