import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'orders/settings.py'
import django
django.setup()
from django.test import TestCase
from rest_framework.test import APIClient


class ThrottleTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/throttled/"

    def test_anon_throttling(self):
        """
        Проверяем, что после трех запросов не аутентифицированный пользователь получает 429.
        """
        for _ in range(3):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)

        # Четвёртый запрос должен вернуть 429 Too Many Requests
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 429)