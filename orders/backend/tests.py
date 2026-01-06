from django.test import TestCase


import pytest
from django.urls import reverse
from rest_framework.test import APIClient
# from django.contrib.auth.models import User
from .models import ContactInfo, Order, Shop, CustomUser

# Create your tests here.

@pytest.mark.django_db
def test_register_account_success():
    """Тест успешной регистрации пользователя."""
    client = APIClient()
    url = reverse('register-account')  # Название эндпоинта в urls.py

    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "nemoymoy@yandex.ru",
        "password": "StrongPassword123!",
        "company": "Example Inc",
        "position": "Manager"
    }

    response = client.post(url, data)

    assert response.status_code == 200
    assert response.json().get('Status') is True


@pytest.mark.django_db
def test_register_account_missing_fields():
    """Тест регистрации с отсутствующими обязательными полями."""
    client = APIClient()
    url = reverse('register-account')

    data = {
        "first_name": "John",
        "email": "johndoe@example.com"
    }

    response = client.post(url, data)

    assert response.status_code == 200
    assert response.json().get('Status') is False
    assert 'Errors' in response.json()


@pytest.mark.django_db
def test_register_account_weak_password():
    """Тест регистрации с простым паролем, который не проходит валидацию."""
    client = APIClient()
    url = reverse('register-account')

    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "password": "123",
        "company": "Example Inc",
        "position": "Manager"
    }

    response = client.post(url, data)

    assert response.status_code == 200
    assert response.json().get('Status') is False
    assert 'password' in response.json().get('Errors', {})


@pytest.mark.django_db
def test_login_account_success():
    """Тест успешного входа пользователя."""
    client = APIClient()
    url = reverse('login-account')

    # Создаем пользователя
    user = CustomUser.objects.create_user(email="johndoe@example.com", password="StrongPassword123!")

    data = {
        "email": "nemoymoy@yandex.ru",
        "password": "StrongPassword123!"
    }

    response = client.post(url, data)

    assert response.status_code == 200
    assert "Вы вошли в систему." in response.content.decode()


@pytest.mark.django_db
def test_contact_view_get_authenticated():
    """Тест получения контактов авторизованного пользователя."""
    client = APIClient()
    url = reverse('contact-view')

    # Создаем пользователя и контакт
    user = CustomUser.objects.create_user(email="nemoymoy@yandex.ru", password="StrongPassword123!")
    client.force_authenticate(user=user)

    ContactInfo.objects.create(user=user, city="City", street="Street", phone="1234567890")

    response = client.get(url)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['city'] == "City"


@pytest.mark.django_db
def test_basket_view_get_authenticated():
    """Тест получения корзины авторизованного пользователя."""
    client = APIClient()
    url = reverse('basket-view')

    # Создаем пользователя и корзину
    user = CustomUser.objects.create_user(email="nemoymoy@yandex.ru", password="StrongPassword123!")
    client.force_authenticate(user=user)

    order = Order.objects.create(user=user, state="basket")

    response = client.get(url)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['id'] == order.id


@pytest.mark.django_db
def test_shop_create_success():
    """Тест успешного создания магазина."""
    client = APIClient()
    url = reverse('shop-create')

    # Создаем пользователя
    user = CustomUser.objects.create_user(email="nemoymoy@yandex.ru", password="StrongPassword123!", is_active=True)
    client.force_authenticate(user=user)

    data = {
        "name": "Test Shop",
        "email": "shop@example.com",
        "address": "123 Test Street"
    }

    response = client.post(url, data)

    assert response.status_code == 201
    assert response.json().get('name') == "Test Shop"
