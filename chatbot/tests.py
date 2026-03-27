from django.test import TestCase, Client
from django.urls import reverse
from events.models import Event, Category
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatbotTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = Category.objects.create(name='Tech', slug='tech')
        self.event = Event.objects.create(
            title='Tech Workshop',
            description='A cool tech workshop',
            date=timezone.now().date() + timedelta(days=5),
            time=timezone.now().time(),
            location='Online',
            capacity=100,
            organizer=self.user,
            category=self.category
        )

    def test_ask_greeting(self):
        response = self.client.post(
            reverse('chatbot:ask'),
            data={'message': 'hello'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello!', response.json()['text'])

    def test_ask_events(self):
        response = self.client.post(
            reverse('chatbot:ask'),
            data={'message': 'upcoming events'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['type'], 'event_list')
        self.assertTrue(len(response.json()['events']) > 0)
        self.assertEqual(response.json()['events'][0]['title'], 'Tech Workshop')

    def test_ask_search(self):
        response = self.client.post(
            reverse('chatbot:ask'),
            data={'message': 'Workshop'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['type'], 'event_list')
        self.assertIn('Tech Workshop', response.json()['events'][0]['title'])

    def test_ask_platform_info(self):
        response = self.client.post(
            reverse('chatbot:ask'),
            data={'message': 'how to register'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('create an account', response.json()['text'].lower())
