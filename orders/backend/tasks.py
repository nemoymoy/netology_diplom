from celery import shared_task
# from easy_thumbnails.files import get_thumbnailer

# from django.core.mail import send_mail
# from django_rest_passwordreset.models import ResetPasswordToken
from celery import shared_task

from .models import AdditionResult


# from django.core.exceptions import ValidationError
# from django.contrib.auth.password_validation import validate_password, get_password_validators
# from django.conf import settings
# from .signals import pre_password_reset, post_password_reset


# @shared_task
# def send_reset_password_email(token_id):
#     try:
#         token = ResetPasswordToken.objects.get(id=token_id)
#         subject = "Восстановление пароля"
#         message = f"Для восстановления пароля перейдите по ссылке: {token.reset_url}"
#         send_mail(subject, message, 'noreply@example.com', [token.email])
#     except ResetPasswordToken.DoesNotExist:
#         print("Токен не найден")

# @shared_task
# def reset_password_task(password, token):
#     reset_password_token = ResetPasswordToken.objects.filter(key=token).first()
#     if reset_password_token and reset_password_token.user.eligible_for_reset():
#         pre_password_reset.send(sender=reset_password_task, user=reset_password_token.user,
#                                 reset_password_token=reset_password_token)
#         try:
#             validate_password(password, user=reset_password_token.user,
#                               password_validators=get_password_validators(settings.AUTH_PASSWORD_VALIDATORS))
#         except ValidationError as e:
#             raise ValidationError({'password': e.messages})
#
#         reset_password_token.user.set_password(password)
#         reset_password_token.user.save()
#         post_password_reset.send(sender=reset_password_task, user=reset_password_token.user,
#                                  reset_password_token=reset_password_token)
#         ResetPasswordToken.objects.filter(user=reset_password_token.user).delete()
#     return {'status': 'OK'}

# @shared_task
# def create_thumbnail_for_product(product_id, model):
#     product = model.objects.get(id=product_id)
#     if product.image:
#         thumbnailer = get_thumbnailer(product.image)
#         thumbnail = thumbnailer.get_thumbnail({'size': (100, 100), 'crop': True})
#         thumbnail.save()
#
# @shared_task
# def create_thumbnail_for_user_avatar(user_id, model):
#     user_profile = model.objects.get(user_id=user_id)
#     if user_profile.avatar:
#         thumbnailer = get_thumbnailer(user_profile.avatar)
#         thumbnail = thumbnailer.get_thumbnail({'size': (100, 100), 'crop': True})
#         thumbnail.save()

result = 1

@shared_task
def add_numbers():
    global result
    print("Running add numbers periodic task")
    result += result
    AdditionResult.objects.create(answer=result)
