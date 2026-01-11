from celery import shared_task
import requests
from yaml import load as load_yaml, Loader
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from urllib.parse import quote

from .models import Shop, Category, Product, Parameter, ProductParameter, ProductInfo

@shared_task
def send_email(token, email):
    list_to = list()
    list_to.append(email)
    print(token, email)
    confirmation_link = f"http://127.0.0.1:1337/api/v1/user/confirm-email/?token={quote(token)}&email={quote(email)}"
    try:
        subject = 'Пожалуйста, подтвердите свой адрес электронной почты'
        message = f'Чтобы подтвердить свой адрес электронной почты, перейдите по этой ссылке: {confirmation_link}'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, email)
        print(subject, message, settings.DEFAULT_FROM_EMAIL, email)
    except Exception as e:
        raise e

@shared_task
def get_import(partner, url):
    if url:
        validate_url = URLValidator()
        try:
            validate_url(url)
        except ValidationError as e:
            return {'Status': False, 'Error': str(e)}
        else:
            stream = requests.get(url).content
        data = load_yaml(stream, Loader=Loader)
        try:
            shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=partner)
        except IntegrityError as e:
            return {'Status': False, 'Error': str(e)}
        for category in data['categories']:
            category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
            category_object.shops.add(shop.id)
            category_object.save()
        ProductInfo.objects.filter(shop_id=shop.id).delete()
        for item in data['goods']:
            product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
            product_info = ProductInfo.objects.create(
                product_id=product.id, external_id=item['id'],
                model=item['model'], price=item['price'],
                price_rrc=item['price_rrc'], quantity=item['quantity'],
                shop_id=shop.id
            )
            for name, value in item['parameters'].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(
                    product_info_id=product_info.id,
                    parameter_id=parameter_object.id, value=value
                )
        return {'Status': True}
    return {'Status': False, 'Errors': 'Url-адрес является ложным'}
