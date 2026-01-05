from django.urls import path

from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

from .views import (PartnerUpdate, RegisterAccount, LoginAccount, CategoryView, ShopView, ProductInfoView, BasketView,
                    AccountDetails, ContactView, OrderView, PartnerStatus, PartnerOrders, ConfirmAccount, ConfirmEmail,
                    DeleteAccount, ShopCreate, ShopStatus, )

app_name = 'backend'

urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'), # Регистрация методом POST
    path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'), # Подтверждение Пользователя методом POST
    path('user/confirm-email/', ConfirmEmail.as_view(), name='confirm-email'),  # Подтверждения E-mail методом GET
    path('user/login', LoginAccount.as_view(), name='user-login'), # Для авторизации пользователей
    path('user/delete/<int:user_id>/', DeleteAccount.as_view(), name='user-delete'),  # Удаление аккаунта пользователя
    path('user/details', AccountDetails.as_view(), name='user-details'), # Для управления данными пользователя
    path('user/contact', ContactView.as_view(), name='user-contact'), # Для управления контактной информацией пользователя

    path('user/password_reset', reset_password_request_token, name='password-reset'), # Посылает токен сброса пароля на электронный адрес пользователя
    path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'), # Проверяет действительность токена и, если все в порядке, обновляет пароль пользователя в системе

    path('shops', ShopView.as_view(), name='shops'), # Для просмотра списка магазинов
    path('shop/create', ShopCreate.as_view(), name='shop_create'),  # Создание магазина
    path('shop/state', ShopStatus.as_view(), name='shop-state'),  # Класс изменения статуса магазина

    path('products', ProductInfoView.as_view(), name='product-search'), # Для поиска товаров
    path('categories', CategoryView.as_view(), name='categories'), # Для просмотра категорий
    path('order', OrderView.as_view(), name='order'), # Для получения и размещения заказов пользователями
    path('basket', BasketView.as_view(), name='basket'), # Для управления корзиной покупок пользователя

    path('partner/update', PartnerUpdate.as_view(), name='partner-update'), # Для обновления прайса поставщика
    path('partner/status', PartnerStatus.as_view(), name='partner-status'), # Для обновления статуса поставщика
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'), # Для получения заказов поставщиками





]