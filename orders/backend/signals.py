from typing import Type

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.core.mail import send_mail
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created
from django.contrib.auth import get_user_model
from urllib.parse import quote
from .models import ConfirmEmailToken, CustomUser

User = get_user_model()

new_user_registered = Signal() # Уведомляет о создании нового пользователя.
new_order = Signal() # Уведомляет о создании нового заказа.
pre_password_reset = Signal()  # providing_args=["user", "reset_password_token"]
post_password_reset = Signal()  # providing_args=["user", "reset_password_token"]

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    msg = EmailMultiAlternatives(subject=f"Password Reset Token for {reset_password_token.user}",
                                 body=reset_password_token.key, from_email=settings.EMAIL_HOST_USER,
                                 to=[reset_password_token.email])
    msg.send()

@receiver(post_save, sender=CustomUser)
def new_user_registered_signal(sender: Type[CustomUser], instance: CustomUser, created: bool, **kwargs):
    if created and not instance.is_active:
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)
        msg = EmailMultiAlternatives(subject=f"Password Reset Token for {instance.email}", body=token.key,
                                     from_email=settings.EMAIL_HOST_USER, to=[instance.email])
        msg.send()

@receiver(post_save, sender=CustomUser)
def authorization(sender, instance, created, **kwargs):
    if created:
        token = ConfirmEmailToken.objects.create(user=instance)
        email = instance.email
        confirmation_link = f"http://127.0.0.1:8000/api/v1/user/confirm-email/?token={quote(token.key)}&email={quote(email)}"
        subject = 'Пожалуйста, подтвердите свой адрес электронной почты'
        message = f'Чтобы подтвердить свой адрес электронной почты, перейдите по этой ссылке: {confirmation_link}'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email])

@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    user = CustomUser.objects.get(id=user_id)
    msg = EmailMultiAlternatives(subject=f"Обновление статуса заказа", body='Заказ сформирован',
                                 from_email=settings.EMAIL_HOST_USER, to=[user.email])
    msg.send()

@receiver(pre_password_reset)
def handle_pre_password_reset(sender, **kwargs):
    user = kwargs['user']
    print(f"Процесс сброса пароля запущен для пользователя: {user}")

@receiver(post_password_reset)
def handle_post_password_reset(sender, **kwargs):

    user = kwargs['user']
    print(f"Процесс сброса пароля для пользователя завершен: {user}")