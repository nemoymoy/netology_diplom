# Верстальщик
from rest_framework import serializers

from .models import CustomUser, Category, Shop, Product, ProductInfo, ProductParameter, ContactInfo, Order, OrderItem

from rest_framework.validators import UniqueValidator
from django.contrib.auth import password_validation
from django.contrib.auth.validators import UnicodeUsernameValidator


class ContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInfo
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'user', 'phone')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }

class UserSerializer(serializers.ModelSerializer):
    contacts = ContactInfoSerializer(read_only=True, many=True)
    email = serializers.EmailField(validators=[UniqueValidator(queryset=CustomUser.objects.all())])
    first_name = serializers.CharField(validators=[UnicodeUsernameValidator()])
    last_name = serializers.CharField(validators=[UnicodeUsernameValidator()])
    username = serializers.CharField(validators=[UniqueValidator(queryset=CustomUser.objects.all())])

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'company', 'position', 'is_active', 'contacts')
        read_only_fields = ('id',)

class UserCreateSerializer(UserSerializer):
    password = serializers.CharField(validators=[password_validation.validate_password])
    email = serializers.EmailField(validators=[UniqueValidator(queryset=CustomUser.objects.all())])
    username = serializers.CharField(validators=[UniqueValidator(queryset=CustomUser.objects.all())])

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'password', 'email', 'company', 'position', 'is_active')
        read_only_fields = ('id',)

class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(validators=[password_validation.validate_password])

    class Meta:
        model = CustomUser
        fields = ('id', 'password', 'email')
        read_only_fields = ('id',)

class ShopSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(default=True)
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'user', 'status',)
        read_only_fields = ('id',)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category',)
        read_only_fields = ('id',)

class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value',)

class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'model', 'external_id', 'product', 'shop', 'quantity', 'price', 'price_rrc',
                  'product_parameters')
        read_only_fields = ('id',)

class OrderItemSerializer(serializers.ModelSerializer):
    product_info = serializers.PrimaryKeyRelatedField(queryset=ProductInfo.objects.all())
    quantity = serializers.IntegerField(min_value=1, max_value=1000, default=1)

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order',)
        read_only_fields = ('id',)
        extra_kwargs = {'order': {'write_only': True}}

class OrderItemUpdSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=OrderItem.objects.all())
    quantity = serializers.IntegerField(min_value=1, max_value=1000, default=1)

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order',)
        read_only_fields = ('id',)
        extra_kwargs = {'order': {'write_only': True}}

class OrderItemCreateSerializer(OrderItemSerializer):
    product_info = ProductInfoSerializer(read_only=True)

class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemCreateSerializer(read_only=True, many=True)
    status = serializers.CharField(required=False, read_only=True)
    total_sum = serializers.IntegerField()
    contact = ContactInfoSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'status', 'dt', 'total_sum', 'contact',)
        read_only_fields = ('id',)

class OrderUpdSerializer(OrderSerializer):
    contact = serializers.IntegerField()

class OrderDelSerializer(serializers.ModelSerializer):
    ordered_items = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=1000))

    class Meta:
        model = Order
        fields = ('id', 'ordered_items')
        read_only_fields = ('id', 'ordered_items')