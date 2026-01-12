import pytest
from rest_framework.test import APIClient
from model_bakery import baker
from .models import CustomUser, ConfirmEmailToken, Shop, Order, OrderItem, ProductInfo, Product, Category, ContactInfo


@pytest.fixture
def api_client():
    client = APIClient()
    return client


@pytest.fixture
def user_factory():
    def factory(**kwargs):
        return baker.make(CustomUser, **kwargs)

    return factory


@pytest.fixture
def confirm_email_token_factory():
    def factory(**kwargs):
        return baker.make(ConfirmEmailToken, **kwargs)

    return factory


@pytest.fixture
def shop_factory():
    def factory(**kwargs):
        return baker.make(Shop, **kwargs)

    return factory


@pytest.fixture
def order_factory():
    def factory(**kwargs):
        return baker.make(Order, **kwargs)

    return factory


@pytest.fixture
def order_item_factory():
    def factory(**kwargs):
        return baker.make(OrderItem, **kwargs)

    return factory


@pytest.fixture
def product_info_factory():
    def factory(**kwargs):
        return baker.make(ProductInfo, **kwargs)

    return factory


@pytest.fixture
def product_factory():
    def factory(**kwargs):
        return baker.make(Product, **kwargs)

    return factory


@pytest.fixture
def category_factory():
    def factory(**kwargs):
        return baker.make(Category, **kwargs)

    return factory


@pytest.fixture
def contact_factory():
    def factory(**kwargs):
        return baker.make(ContactInfo, **kwargs)

    return factory