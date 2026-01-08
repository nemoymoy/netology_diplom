
from django.shortcuts import render
from ujson import loads as load_json
from yaml import load as load_yaml, Loader
from requests import get
from distutils.util import strtobool
from ast import literal_eval

from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.password_validation import validate_password
from django.http import JsonResponse, Http404
from django.contrib.auth import authenticate
from django.db.models import Q, Sum, F
from django.db import IntegrityError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import URLValidator

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework import status

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import (Shop, CustomUser, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, ContactInfo,
                     ConfirmEmailToken)
from .serializers import (UserSerializer, CategorySerializer, ShopSerializer, ContactInfoSerializer,
                          ProductInfoSerializer, OrderSerializer, OrderItemSerializer)
from .signals import new_order


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


# Create your views here.

class RegisterAccount(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if {'username', 'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

class ConfirmAccount(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True}, status=200)
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'}, status=400)
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

class ConfirmEmail(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        email = request.query_params.get('email')
        token = request.query_params.get('token')
        if email and token:
            confirm_email_token = ConfirmEmailToken.objects.filter(user__email=email, key=token).first()
            if confirm_email_token:
                confirm_email_token.user.is_active = True
                confirm_email_token.user.save()
                confirm_email_token.delete()
                return Response({'Status': True})
            else:
                return Response({'Status': False, 'Errors': 'Неправильно указан токен или email'}, status=400)
        else:
            return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

class LoginAccount(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return JsonResponse({'Status': True, 'Token': token.key}, status=200)
                else:
                    return JsonResponse({'Status': False, 'Errors': 'Пользователь не активен'}, status=403)
            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'}, status=401)
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

class DeleteAccount(GenericAPIView):
    queryset = CustomUser.objects.all()
    def get_object(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            raise Http404("Пользователь не существует")
    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs['user_id']
        user = self.get_object(user_id)
        user.delete()
        return Response({'Status': True}, status=204)

class AccountDetails(APIView):
    @staticmethod
    def get(request: Request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if 'password' in request.data:
            errors = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

class ContactView(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        contact = ContactInfo.objects.filter(
            user_id=request.user.id)
        serializer = ContactInfoSerializer(contact, many=True)
        return Response(serializer.data)
    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if {'city', 'street', 'phone'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactInfoSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)
    @staticmethod
    def delete(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = ContactInfo.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)
    @staticmethod
    def put(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = ContactInfo.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                print(contact)
                if contact:
                    serializer = ContactInfoSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True})
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

class ShopView(ListAPIView):
    queryset = Shop.objects.filter(status=True)
    # serializer_class = ShopSerializer
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.queryset)
        return Response(serializer.data)

class ShopCreate(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if 'email' not in request.data:
            return JsonResponse({'Status': False, 'Error': 'Требуется Email'}, status=400)
        email = request.data['email']
        try:
            user = CustomUser.objects.get(email=email)
        except ObjectDoesNotExist:
            return JsonResponse({'Status': False, 'Error': 'Пользователь не существует'}, status=404)
        if not user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if 'password' in request.data:
            errors = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(str(item))
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
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
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)
    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        status = request.data.get('status')
        if status:
            try:
                Shop.objects.filter(user_id=request.user.id).update(status=literal_eval(status))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

class ProductInfoView(APIView):
    @staticmethod
    def get(request: Request, *args, **kwargs):
        query = Q(shop__status=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')
        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        queryset = ProductInfo.objects.filter(query).select_related('shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data)

class CategoryView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class OrderView(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        order = Order.objects.filter(
            user_id=request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        status='new')
                except IntegrityError as error:
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'}, status=403)
                else:
                    if is_updated:
                        new_order.send(sender=self.__class__, user_id=request.user.id)
                        return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

class BasketView(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)
    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return JsonResponse({'Status': False, 'Errors': str(error)})
                        else:
                            objects_created += 1
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})
                return JsonResponse({'Status': True, 'Создано объектов': objects_created})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)
    @staticmethod
    def delete(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)
    @staticmethod
    def put(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])
                return JsonResponse({'Status': True, 'Обновлено объектов': objects_updated})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

class PartnerUpdate(APIView):
    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content
                data = load_yaml(stream, Loader=Loader)
                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)
                return JsonResponse({'Status': True})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

class PartnerStatus(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)
    @staticmethod
    def post(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        status = request.data.get('status')
        if status:
            try:
                Shop.objects.filter(user_id=request.user.id).update(status=strtobool(status))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}, status=400)

class PartnerOrders(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется войти в систему'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        order = Order.objects.filter(
            ordered_items__product_info__shop__user_id=request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)



@login_required(login_url="/login")
def home_page(request):
    return render(request, 'home.html')


def index_page(request):
    return render(request, 'index.html')


def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Invalid Username')
            return redirect('/login')
        user = authenticate(email=email, password=password)
        if user is None:
            messages.error(request, "Invalid Password")
            return redirect('/login')
        else:
            login(request, user)
            return redirect('/home')
    return render(request, 'login.html')


def register_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        user = CustomUser.objects.filter(username=username)
        if user.exists():
            messages.info(request, "Username already taken!")
            return redirect('/register')
        user = CustomUser.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=username
        )
        user.set_password(password)
        user.save()
        messages.info(request, "Account created Successfully!")
        return redirect('/register')
    return render(request, 'register.html')

@login_required
def logout_handler(request):
    logout(request)
    return redirect('/')
