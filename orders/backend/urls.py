from django.urls import path
from django_rest_passwordreset.views import (
    reset_password_request_token,
    reset_password_confirm,
)
from rest_framework.routers import DefaultRouter

from .views import (
    PartnerUpdate,
    RegisterAccount,
    LoginAccount,
    CategoryView,
    ShopView,
    ProductInfoView,
    BasketView,
    AccountDetails,
    ContactView,
    OrderView,
    PartnerStatus,
    PartnerOrders,
    ConfirmAccount,
    ConfirmEmail,
    DeleteAccount,
    ShopCreate,
    ShopStatus,
    PartnerUpdateTask,
    RegisterAccountTask,
    HomeView,
    avatar_user,
    edit_image_user,
    avatar_product,
    edit_image_product,
    RollbarTestView,
)

app_name = "backend"
r = DefaultRouter()
urlpatterns = r.urls
urlpatterns += [
    path("", HomeView.as_view(), name="home"),
    path(
        "user/register", RegisterAccount.as_view(), name="user-register"
    ),  # Регистрация методом POST
    path(
        "user/register_task", RegisterAccountTask.as_view(), name="user-register-task"
    ),  # Регистрация методом POST с подтверждением через email
    path(
        "user/register/confirm", ConfirmAccount.as_view(), name="user-register-confirm"
    ),  # Подтверждение Пользователя методом POST
    path(
        "user/confirm-email/", ConfirmEmail.as_view(), name="confirm-email"
    ),  # Подтверждения E-mail методом GET
    path(
        "user/login", LoginAccount.as_view(), name="user-login"
    ),  # Для авторизации пользователей
    path(
        "user/delete/<int:user_id>/", DeleteAccount.as_view(), name="user-delete"
    ),  # Удаление аккаунта пользователя
    path(
        "user/details", AccountDetails.as_view(), name="user-details"
    ),  # Для управления данными пользователя
    path(
        "user/contact", ContactView.as_view(), name="user-contact"
    ),  # Для управления контактной информацией пользователя
    path(
        "user/password_reset", reset_password_request_token, name="password-reset"
    ),  # Посылает токен сброса пароля на электронный адрес пользователя
    path(
        "user/password_reset/confirm",
        reset_password_confirm,
        name="password-reset-confirm",
    ),  # Проверяет действительность токена и, если все в порядке, обновляет пароль пользователя в системе
    path("shops", ShopView.as_view(), name="shops"),  # Для просмотра списка магазинов
    path("shop/create", ShopCreate.as_view(), name="shop-create"),  # Создание магазина
    path(
        "shop/state", ShopStatus.as_view(), name="shop-status"
    ),  # Класс изменения статуса магазина
    path(
        "products", ProductInfoView.as_view(), name="product-search"
    ),  # Для поиска товаров
    path(
        "categories", CategoryView.as_view(), name="categories"
    ),  # Для просмотра категорий
    path(
        "order", OrderView.as_view(), name="order"
    ),  # Для получения и размещения заказов пользователями
    path(
        "basket", BasketView.as_view(), name="basket"
    ),  # Для управления корзиной покупок пользователя
    path(
        "partner/update", PartnerUpdate.as_view(), name="partner-update"
    ),  # Для обновления прайса поставщика
    path(
        "partner/update_task", PartnerUpdateTask.as_view(), name="partner-update-task"
    ),  # Для обновления прайса поставщика
    path(
        "partner/status", PartnerStatus.as_view(), name="partner-status"
    ),  # Для обновления статуса поставщика
    path(
        "partner/orders", PartnerOrders.as_view(), name="partner-orders"
    ),  # Для получения заказов поставщиками
    path(
        "avatar_user", avatar_user, name="avatar_user"
    ),  # Для загрузки аватара Пользователя
    path(
        "edit_image_user/<int:pk>/", edit_image_user, name="edit_image_user"
    ),  # Для редактирования аватара Пользователя
    path(
        "avatar_product", avatar_product, name="avatar_product"
    ),  # Для загрузки изображения продукта
    path(
        "edit_image_product/<int:pk>/", edit_image_product, name="edit_image_product"
    ),  # Для редактирования изображения продукта
    path(
        "test-rollbar/", RollbarTestView.as_view(), name="test-rollbar"
    ),  # Для тестирования rollbar
]
