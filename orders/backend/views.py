import json
import requests
from ujson import loads as load_json
from yaml import load as load_yaml, Loader
from urllib.parse import quote
from distutils.util import strtobool
from ast import literal_eval
import rollbar

from django.contrib.auth.password_validation import validate_password
from django.http import JsonResponse, Http404, HttpResponse
from django.db.models import Q, Sum, F
from django.db import IntegrityError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import URLValidator
from django.contrib.auth import authenticate
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect, render

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework import status

from .forms import AvatarUserImageForm, AvatarProductImageForm
from .models import (
    Shop,
    CustomUser,
    Category,
    Product,
    ProductInfo,
    Parameter,
    ProductParameter,
    Order,
    OrderItem,
    ContactInfo,
    ConfirmEmailToken,
    AvatarUser,
    AvatarProduct,
)
from .serializers import (
    UserSerializer,
    CategorySerializer,
    ShopSerializer,
    ContactInfoSerializer,
    ProductInfoSerializer,
    OrderSerializer,
    OrderItemSerializer,
)

from .tasks import (
    send_email,
    get_import,
    create_thumbnail_for_avatar_user,
    create_thumbnail_for_avatar_product,
    test_rollbar,
)


# Create your views here.


class HomeView(TemplateView):
    template_name = "home.html"


class RegisterAccount(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if {
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "company",
            "position",
        }.issubset(request.data):
            try:
                validate_password(request.data["password"])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse(
                    {"Status": False, "Errors": {"password": error_array}},
                    status=status.HTTP_403_FORBIDDEN,
                )
            else:
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data["password"])
                    user.save()
                    return JsonResponse(
                        {"Status": True}, status=status.HTTP_201_CREATED
                    )
                else:
                    return JsonResponse(
                        {"Status": False, "Errors": user_serializer.errors},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RegisterAccountTask(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if {
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "company",
            "position",
        }.issubset(request.data):
            try:
                validate_password(request.data["password"])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse(
                    {"Status": False, "Errors": {"password": error_array}},
                    status=status.HTTP_403_FORBIDDEN,
                )
            else:
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data["password"])
                    user.save()
                    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
                    confirmation_link = (
                        f"http://127.0.0.1:1337/api/v1/user/confirm-email/?token={quote(token.key)}"
                        f"&email={quote(user.email)}"
                    )
                    subject = "Пожалуйста, подтвердите свой адрес электронной почты"
                    message = f"Чтобы подтвердить свой адрес электронной почты, перейдите по этой ссылке: {confirmation_link}"
                    send_email.delay(subject, message, user.email)
                    return JsonResponse(
                        {
                            "Status": True,
                            "Токен для подтверждения по электронной почте": token.key,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return JsonResponse(
                        {"Status": False, "Errors": user_serializer.errors},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ConfirmAccount(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if {"email", "token"}.issubset(request.data):
            token = ConfirmEmailToken.objects.filter(
                user__email=request.data["email"], key=request.data["token"]
            ).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({"Status": True})
            else:
                return JsonResponse(
                    {"Status": False, "Errors": "Неправильно указан токен или email"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ConfirmEmail(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        email = request.query_params.get("email")
        token = request.query_params.get("token")
        if email and token:
            confirm_email_token = ConfirmEmailToken.objects.filter(
                user__email=email, key=token
            ).first()
            if confirm_email_token:
                confirm_email_token.user.is_active = True
                confirm_email_token.user.save()
                confirm_email_token.delete()
                return Response({"Status": True})
            else:
                return Response(
                    {"Status": False, "Errors": "Неправильно указан токен или email"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        else:
            return Response(
                {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginAccount(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if {"email", "password"}.issubset(request.data):
            user = authenticate(
                request,
                username=request.data["email"],
                password=request.data["password"],
            )
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return JsonResponse(
                        {"Status": True, "Token": token.key}, status=status.HTTP_200_OK
                    )
                else:
                    return JsonResponse(
                        {"Status": False, "Errors": "Пользователь не активен"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            return JsonResponse(
                {"Status": False, "Errors": "Не удалось авторизовать"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class DeleteAccount(GenericAPIView):
    queryset = CustomUser.objects.all()

    def get_object(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            raise Http404("Пользователь не существует")

    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs["user_id"]
        user = self.get_object(user_id)
        user.delete()
        return Response({"Status": True}, status=status.HTTP_204_NO_CONTENT)


class AccountDetails(APIView):
    @staticmethod
    def get(request: Request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if {"password"}.issubset(request.data):
            if "password" in request.data:
                try:
                    validate_password(request.data["password"])
                except Exception as password_error:
                    return JsonResponse(
                        {"Status": False, "Errors": {"password": password_error}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                request.user.set_password(request.data["password"])
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({"Status": True}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(
                {"Status": False, "Errors": user_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ContactView(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        contact = ContactInfo.objects.filter(user_id=request.user.id)
        serializer = ContactInfoSerializer(contact, many=True)
        return Response(serializer.data)

    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if {"city", "street", "phone"}.issubset(request.data):
            request.POST._mutable = True
            request.data.update({"user": request.user.id})
            serializer = ContactInfoSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({"Status": True}, status=status.HTTP_201_CREATED)
            else:
                JsonResponse(
                    {"Status": False, "Error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return JsonResponse(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @staticmethod
    def put(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if {"id"}.issubset(request.data):
            try:
                contact = get_object_or_404(ContactInfo, pk=int(request.data["id"]))
            except ValueError:
                return JsonResponse(
                    {"Status": False, "Error": "Недопустимый идентификатор типа ID."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = ContactInfoSerializer(contact, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({"Status": True}, status=status.HTTP_200_OK)
            return JsonResponse(
                {"Status": False, "Error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return JsonResponse(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @staticmethod
    def delete(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if {"items"}.issubset(request.data):
            for item in request.data["items"].split(","):
                try:
                    contact = get_object_or_404(ContactInfo, pk=int(item))
                    contact.delete()
                except ValueError:
                    return JsonResponse(
                        {
                            "Status": False,
                            "Error": "Недопустимый тип аргумента (items).",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                except ObjectDoesNotExist:
                    return JsonResponse(
                        {"Status": False, "Error": f"Нет контакта с ID{item}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            return JsonResponse({"Status": True}, status=status.HTTP_200_OK)
        return JsonResponse(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ShopView(ListAPIView):
    queryset = Shop.objects.filter(status=True)
    serializer_class = ShopSerializer


class ShopCreate(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if "email" not in request.data:
            return JsonResponse(
                {"Status": False, "Error": "Требуется Email"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        email = request.data["email"]
        try:
            user = CustomUser.objects.get(email=email)
        except ObjectDoesNotExist:
            return JsonResponse(
                {"Status": False, "Error": "Пользователь не существует"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if "password" in request.data:
            errors = {}
            try:
                validate_password(request.data["password"])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(str(item))
                return JsonResponse(
                    {"Status": False, "Errors": {"password": error_array}}
                )
        serializer = ShopSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopStatus(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.type != "shop":
            return JsonResponse(
                {"Status": False, "Error": "Только для магазинов"},
                status=status.HTTP_403_FORBIDDEN,
            )
        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.type != "shop":
            return JsonResponse(
                {"Status": False, "Error": "Только для магазинов"},
                status=status.HTTP_403_FORBIDDEN,
            )
        my_status = request.data.get("status")
        if my_status:
            try:
                Shop.objects.filter(user_id=request.user.id).update(
                    status=literal_eval(my_status)
                )
                return JsonResponse({"Status": True})
            except ValueError as error:
                return JsonResponse({"Status": False, "Errors": str(error)})

        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProductInfoView(APIView):
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer
    http_method_names = [
        "get",
    ]

    @staticmethod
    def get(request: Request, *args, **kwargs):
        query = Q(shop__status=True)
        shop_id = request.query_params.get("shop_id")
        category_id = request.query_params.get("category_id")
        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        queryset = (
            ProductInfo.objects.filter(query)
            .select_related("shop", "product__category")
            .prefetch_related("product_parameters__parameter")
            .distinct()
        )
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data)


class CategoryView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class OrderView(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        order = (
            Order.objects.filter(user_id=request.user.id)
            .exclude(status="basket")
            .prefetch_related(
                "ordered_items__product_info__product__category",
                "ordered_items__product_info__product_parameters__parameter",
            )
            .select_related("contact")
            .annotate(
                total_sum=Sum(
                    F("ordered_items__quantity")
                    * F("ordered_items__product_info__price")
                )
            )
            .distinct()
            .order_by("-date")
        )
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    @staticmethod
    def post(request, *args, **kwargs):
        if {"id", "contact"}.issubset(request.data):
            if request.data["id"].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data["id"]
                    ).update(contact_id=request.data["contact"], status="new")
                except IntegrityError as error:
                    return JsonResponse(
                        {
                            "Status": False,
                            "Errors": f"Неверно указаны аргументы {error}",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    if is_updated:
                        subject = "Обновление статуса заказа"
                        message = "Заказ сформирован"
                        send_email.delay(subject, message, request.user.email)
                        return JsonResponse({"Status": True}, status=status.HTTP_200_OK)
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BasketView(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        basket = (
            Order.objects.filter(user_id=request.user.id, status="basket")
            .prefetch_related(
                "ordered_items__product_info__product_parameters__parameter"
            )
            .annotate(
                total_sum=Sum(
                    F("ordered_items__quantity")
                    * F("ordered_items__product_info__price")
                )
            )
            .distinct()
        )
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    @staticmethod
    def post(request, *args, **kwargs):
        items = request.data.get("items")
        if items:
            try:
                items_dict = json.dumps(items)
            except ValueError as e:
                JsonResponse(
                    {"Status": False, "Errors": f"Недопустимый формат запроса {e}"}
                )
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id, status="basket"
                )
                objects_created = 0
                for order_item in load_json(items_dict):
                    order_item.update({"order": basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid(raise_exception=True):
                        try:
                            serializer.save()
                        except IntegrityError as e:
                            return JsonResponse({"Status": False, "Errors": str(e)})
                        else:
                            objects_created += 1
                    else:
                        JsonResponse({"Status": False, "Errors": serializer.errors})
                return JsonResponse(
                    {"Status": True, "Создано объектов": objects_created},
                    status=status.HTTP_201_CREATED,
                )
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @staticmethod
    def put(request, *args, **kwargs):
        items_sting = request.data.get("items")
        if items_sting:
            try:
                items_dict = json.dumps(items_sting)
            except ValueError as e:
                JsonResponse(
                    {"Status": False, "Errors": f"Недопустимый формат запроса {e}"}
                )
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id, status="basket"
                )
                objects_updated = 0
                for order_item in json.loads(items_dict):
                    if isinstance(order_item["id"], int) and isinstance(
                        order_item["quantity"], int
                    ):
                        objects_updated += OrderItem.objects.filter(
                            order_id=basket.id, product_info_id=order_item["id"]
                        ).update(quantity=order_item["quantity"])
                return JsonResponse(
                    {"Status": True, "Создано объектов": objects_updated}
                )
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @staticmethod
    def delete(request, *args, **kwargs):
        items = request.data.get("items")
        if items:
            items_list = items.split(",")
            basket, _ = Order.objects.get_or_create(
                user_id=request.user.id, status="basket"
            )
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse(
                    {"Status": True, "Удалено объектов": deleted_count},
                    status=status.HTTP_200_OK,
                )
        return JsonResponse(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PartnerUpdate(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if request.user.type != "shop":
            return JsonResponse(
                {"Status": False, "Error": "Только для магазинов"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        url = request.data.get("url")
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({"Status": False, "Error": str(e)})
            else:
                stream = requests.get(url)
                data = load_yaml(stream.content, Loader=Loader)
                shop, _ = Shop.objects.get_or_create(
                    name=data["shop"], user_id=request.user.id
                )
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
                return JsonResponse({"Status": True})
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PartnerUpdateTask(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.type != "shop":
            return JsonResponse(
                {"Status": False, "Error": "Только для магазинов"},
                status=status.HTTP_403_FORBIDDEN,
            )
        url = request.data.get("url")
        if url:
            try:
                _task = get_import.delay(request.user.id, url)
            except IntegrityError as e:
                return JsonResponse(
                    {"Status": False, "Errors": f"Ошибка целостности: {e}"}
                )
            return JsonResponse({"Status": True}, status=status.HTTP_200_OK)
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PartnerStatus(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.type != "shop":
            return JsonResponse(
                {"Status": False, "Error": "Только для магазинов"},
                status=status.HTTP_403_FORBIDDEN,
            )

        shop = Shop.objects.get(user=request.user.id)
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.type != "shop":
            return JsonResponse(
                {"Status": False, "Error": "Только для магазинов"},
                status=status.HTTP_403_FORBIDDEN,
            )
        my_status = request.data.get("status")
        if my_status:
            try:
                Shop.objects.filter(user_id=request.user.id).update(
                    status=strtobool(my_status)
                )
                return JsonResponse({"Status": True}, status=status.HTTP_200_OK)
            except ValueError as error:
                return JsonResponse({"Status": False, "Errors": str(error)})
        return JsonResponse(
            {"Status": False, "Errors": "Не указаны все необходимые аргументы"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PartnerOrders(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"Status": False, "Error": "Требуется войти в систему"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.type != "shop":
            return JsonResponse(
                {"Status": False, "Error": "Только для магазинов"},
                status=status.HTTP_403_FORBIDDEN,
            )
        order = (
            Order.objects.filter(
                ordered_items__product_info__shop__user_id=request.user.id
            )
            .exclude(status="basket")
            .prefetch_related(
                "ordered_items__product_info__product__category",
                "ordered_items__product_info__product_parameters__parameter",
            )
            .select_related("contact")
            .annotate(
                total_sum=Sum(
                    F("ordered_items__quantity")
                    * F("ordered_items__product_info__price")
                )
            )
            .distinct()
        )
        serializer = OrderSerializer(order, many=True)
        send_email.delay(
            "Обновление статуса заказа", "Заказ обработан", request.user.email
        )
        return Response(serializer.data)


def avatar_user(request):
    if request.method == "POST":
        form = AvatarUserImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            print(request)
            user = form.cleaned_data["user"]
            create_thumbnail_for_avatar_user.delay(user_id=user.id)
            return redirect("backend:avatar_user")
    else:
        form = AvatarUserImageForm()
    images = AvatarUser.objects.all()
    return render(request, "backend/avatar_user.html", {"form": form, "images": images})


def edit_image_user(request, pk):
    image = get_object_or_404(AvatarUser, pk=pk)
    if request.method == "POST":
        form = AvatarUserImageForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            form.save()
            return redirect("backend:avatar_user")
    else:
        form = AvatarUserImageForm(instance=image)
    return render(
        request, "backend/edit_image_user.html", {"form": form, "image": image}
    )


def avatar_product(request):
    if request.method == "POST":
        form = AvatarProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            product = form.cleaned_data["product"]
            create_thumbnail_for_avatar_product.delay(product_id=product.id)
            return redirect("backend:avatar_product")
    else:
        form = AvatarProductImageForm()
    images = AvatarProduct.objects.all()
    return render(
        request, "backend/avatar_product.html", {"form": form, "images": images}
    )


def edit_image_product(request, pk):
    image = get_object_or_404(AvatarProduct, pk=pk)
    if request.method == "POST":
        form = AvatarProductImageForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            form.save()
            return redirect("backend:avatar_product")
    else:
        form = AvatarProductImageForm(instance=image)
    return render(
        request, "backend/edit_image_product.html", {"form": form, "image": image}
    )


class RollbarTestView(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        # a = None
        # a.hello()  # Creating an error with an invalid line of code
        # return HttpResponse("Hello, world. You're at the pollapp index.")

        test_rollbar.delay()
