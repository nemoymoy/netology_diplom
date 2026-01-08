import requests

from django.urls import reverse
from rest_framework.test import APIClient

# Создание пользователя

# print("Создание двух пользователей и одного админа")
# data = requests.post("http://127.0.0.1:8000/api/v1/user", json={"name": "user_1", "password": "12345678"})
# print(data.status_code)
# print(data.json())
# data = requests.post("http://127.0.0.1:8000/api/v1/user", json={"name": "user_2", "password": "67891012"})
# print(data.status_code)
# print(data.json())
# data = requests.post("http://127.0.0.1:8000/api/v1/user", json={"name": "admin",
#                                                                 "password": "admin12345678",
#                                                                 "role": "admin"})
# print(data.status_code)
# print(data.json())

def test_register_account_success():
    """Тест успешной регистрации пользователя."""
    client = APIClient()
    url = reverse('register-account')  # Название эндпоинта в urls.py
    # url = "http://127.0.0.1:1337/api/v1/user/register"

    data = {
        "email": "nemoymoy@yandex.ru",
        "password": "Aa12345678!",
        "company": "Example Inc",
        "position": "Manager",
        "username": "nemo",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "is_staff": True,
        "is_superuser": False,
        "type": "buyer"
    }

    response = client.post(url, data)

    assert response.status_code == 200
    assert response.json().get('Status') is True

if __name__ == "__main__":
    test_register_account_success()