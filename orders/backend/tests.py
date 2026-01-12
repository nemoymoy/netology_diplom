import pytest
from django.urls import reverse

# from rest_framework.test import APIClient
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)

# from .models import ContactInfo, Order, CustomUser


# Create your tests here.


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_register_account_success(api_client):
    """Тест успешной регистрации пользователя."""
    url = reverse(viewname="user-register")
    data = {
        "email": "nemoymoy@yandex.ru",
        "password": "Aa12345678!",
        "company": "Example Inc",
        "position": "Manager",
        "username": "django",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "type": "buyer",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == HTTP_201_CREATED
    assert response.status_code == HTTP_201_CREATED
    assert response.json().get("Status") is True


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_register_account_missing_fields(api_client):
    """Тест регистрации с отсутствующими обязательными полями."""
    url = reverse("user-register")
    data = {"first_name": "John", "email": "nemoymoy@yandex.ru"}
    response = api_client.post(url, data, format="json")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json().get("Status") is False
    assert "Errors" in response.json()


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_register_account_weak_password(api_client):
    """Тест регистрации с простым паролем, который не проходит валидацию."""
    url = reverse("user-register")
    data = {
        "email": "nemoymoy@yandex.ru",
        "password": "123",
        "company": "Example Inc",
        "position": "Manager",
        "username": "django",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "type": "buyer",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == HTTP_403_FORBIDDEN
    assert response.json().get("Status") is False
    assert "password" in response.json().get("Errors", {})


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_user_confirm(api_client, user_factory, confirm_email_token_factory):
    """Тест подтверждения регистрации пользователя по email."""
    user = user_factory()
    token = confirm_email_token_factory(user=user)
    url = reverse("user-register-confirm")
    response = api_client.post(url, data={"email": user.email, "token": "wrong_key"})
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json().get("Status") is False
    response = api_client.post(url, data={"email": user.email, "token": token.key})
    assert response.status_code == HTTP_200_OK
    assert response.json().get("Status") is True


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_login_account_success(api_client):
    """Тест успешного входа пользователя."""
    url = reverse("user-register")
    data = {
        "email": "nemoymoy@yandex.ru",
        "password": "Aa12345678!",
        "company": "Example Inc",
        "position": "Manager",
        "username": "django",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "type": "buyer",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == HTTP_201_CREATED
    assert response.json().get("Status") is True
    url = reverse("user-login")
    data = {"email": "nemoymoy@yandex.ru", "password": "Aa12345678!"}
    response = api_client.post(url, data, format="json")
    assert response.status_code == HTTP_200_OK
    assert response.json().get("Status") is True


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_user_details(api_client, user_factory):
    """Тест запроса и записи деталей аккаунта пользователя."""
    url = reverse("user-details")
    user = user_factory()
    api_client.force_authenticate(user=user)
    response = api_client.get(url)
    assert response.status_code == HTTP_200_OK
    user = user_factory()
    api_client.force_authenticate(user=user)
    response = api_client.post(url)
    assert response.status_code == HTTP_200_OK


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_contact_view_get_authenticated(api_client, user_factory, contact_factory):
    """Тест получения контактов авторизованного пользователя."""
    user = user_factory()
    api_client.force_authenticate(user=user)
    url = reverse("user-contact")
    contact = contact_factory(user=user)
    data = {
        "user_id": user.id,
    }
    response = api_client.get(url, data=data, format="json")
    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["city"] == contact.city


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_shop_create_success(api_client):
    """Тест успешного создания магазина."""
    url = reverse("user-register")
    data = {
        "email": "nemoymoy@yandex.ru",
        "password": "Aa12345678!",
        "company": "Example Inc",
        "position": "Manager",
        "username": "django",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "type": "buyer",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == HTTP_201_CREATED
    assert response.json().get("Status") is True
    api_client.force_authenticate(user=response.json().get("User"))
    url = reverse("shop-create")
    data = {
        "email": "nemoymoy@yandex.ru",
        "password": "Aa12345678!",
        "name": "DNS",
        "url": "https://dns-shop.ru",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == HTTP_201_CREATED
    assert response.json().get("name") == "DNS"


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_products(
    api_client,
    user_factory,
    shop_factory,
    order_factory,
    product_info_factory,
    product_factory,
    category_factory,
):
    """Тест получения информации о магазине и продукции."""
    url = reverse("shops")
    shop = shop_factory()
    customer = user_factory()
    api_client.force_authenticate(user=customer)
    category = category_factory()
    product = product_factory(category=category)
    _product_info = product_info_factory(product=product, shop=shop)
    response = api_client.get(url, shop_id=shop.id, category_id=category.id)
    assert response.status_code == HTTP_200_OK
    assert response.json().get("results")[0]["id"] == 2


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_category_get(api_client, category_factory):
    """Тест получения информации о категориях товаров."""
    url = reverse("categories")
    category_factory(_quantity=4)
    response = api_client.get(url)
    assert response.status_code == HTTP_200_OK
    assert len(response.data) == 4


@pytest.mark.urls("backend.urls")
@pytest.mark.django_db
def test_basket_view_get_authenticated(api_client):
    """Тест получения корзины авторизованного пользователя."""
    url = reverse("user-register")
    data = {
        "email": "nemoymoy@yandex.ru",
        "password": "Aa12345678!",
        "company": "Example Inc",
        "position": "Manager",
        "username": "django",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "type": "buyer",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == HTTP_201_CREATED
    assert response.json().get("Status") is True
    _user = api_client.force_authenticate(user=response.json().get("User"))
    url = reverse("basket")
    data = {
        "status": "basket",
    }
    response = api_client.get(url, data, format="json")
    assert response.status_code == HTTP_200_OK
    assert len(response.json()) == 0
