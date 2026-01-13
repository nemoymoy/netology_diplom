from celery import shared_task
import requests
from easy_thumbnails.files import get_thumbnailer
from yaml import load as load_yaml, Loader
from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import Shop, Category, Product, Parameter, ProductParameter, ProductInfo, AvatarUser, AvatarProduct


@shared_task
def send_email(subject, message, email):
    list_to = list()
    list_to.append(email)
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, list_to)
    except Exception as e:
        raise e


@shared_task
def get_import(partner, url):
    if url:
        validate_url = URLValidator()
        try:
            validate_url(url)
        except ValidationError as e:
            return {"Status": False, "Error": str(e)}
        else:
            stream = requests.get(url).content
        data = load_yaml(stream, Loader=Loader)
        try:
            shop, _ = Shop.objects.get_or_create(name=data["shop"], user_id=partner)
        except IntegrityError as e:
            return {"Status": False, "Error": str(e)}
        for category in data["categories"]:
            category_object, _ = Category.objects.get_or_create(
                id=category["id"], name=category["name"]
            )
            category_object.shops.add(shop.id)
            category_object.save()
        ProductInfo.objects.filter(shop_id=shop.id).delete()
        for item in data["goods"]:
            product, _ = Product.objects.get_or_create(
                name=item["name"], category_id=item["category"]
            )
            product_info = ProductInfo.objects.create(
                product_id=product.id,
                external_id=item["id"],
                model=item["model"],
                price=item["price"],
                price_rrc=item["price_rrc"],
                quantity=item["quantity"],
                shop_id=shop.id,
            )
            for name, value in item["parameters"].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(
                    product_info_id=product_info.id,
                    parameter_id=parameter_object.id,
                    value=value,
                )
        return {"Status": True}
    return {"Status": False, "Errors": "Url-адрес является ложным"}

@shared_task
def create_thumbnail_for_avatar_user(user_id):
    user_profile = AvatarUser.objects.get(user_id=user_id)
    if user_profile.image:
        thumbnailer = get_thumbnailer(user_profile.image)
        thumbnail = thumbnailer.get_thumbnail({
            'size': (100, 100),
            'crop': True,
        })
        # Сохраняем миниатюру (если нужно)
        thumbnail.save()

@shared_task
def create_thumbnail_for_avatar_product(product_id):
    product_profile = AvatarProduct.objects.get(product_id=product_id)
    if product_profile.image:
        thumbnailer = get_thumbnailer(product_profile.image)
        thumbnail = thumbnailer.get_thumbnail({
            'size': (100, 100),
            'crop': True,
        })
        # Сохраняем миниатюру (если нужно)
        thumbnail.save()