
from easy_thumbnails.fields import ThumbnailerImageField
from .tasks import create_thumbnail_for_product, create_thumbnail_for_user_avatar

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.contrib.auth.validators import UnicodeUsernameValidator, ASCIIUsernameValidator
from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator
from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta

import six

USER_TYPE_CHOICES = (('shop', 'Магазин'), ('buyer', 'Покупатель'))

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

# Create your models here.

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='Email', max_length=255, unique=True)
    company = models.CharField(verbose_name='Компания', max_length=40, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=40, blank=True)

    username_validator = UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()

    username = models.CharField(verbose_name='Псевдоним', max_length=150, unique=True,
                                help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
                                validators=[username_validator],
                                error_messages={'unique': _("A user with that username already exists.")}
                                )
    first_name = models.CharField(verbose_name='Имя', max_length=30, blank=True)
    last_name = models.CharField(verbose_name='Фамилия',max_length=30, blank=True)
    is_staff = models.BooleanField(verbose_name="Администратор", default=False,
                                   help_text=_("Designates whether the user can log into this admin site.")
                                   )
    is_active = models.BooleanField(verbose_name="Активен", default=True,
                                    help_text=_("Designates whether this user should be treated as active. "
                                                "Unselect this instead of deleting accounts.")
                                    )
    user_type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5,
                                 default='buyer')
    date_joined = models.DateTimeField(verbose_name="Дата присоединения", default=timezone.now)
    group = models.ManyToManyField(Group, verbose_name='Группа', related_name="group_for_user", blank=True)
    permission = models.ManyToManyField(Permission, verbose_name='Разрешение', related_name="permission_for_user",
                                        blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['email']

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

class Shop(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(verbose_name="Название магазина",max_length=100, null=False, blank=False, unique=True)
    url = models.URLField(verbose_name="URL магазина", null=True, blank=True)
    user = models.OneToOneField(CustomUser, verbose_name='Пользователь', related_name="user_for_shop", null=True,
                                blank=True, on_delete=models.CASCADE)
    status = models.BooleanField(verbose_name="Статус", default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-name']
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'

class Category(models.Model):
    objects = models.manager.Manager()
    shops = models.ManyToManyField(Shop, verbose_name="Магазины", related_name="shops_for_category", blank=True)
    name = models.CharField(verbose_name="Название категории", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-name']
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class Product(models.Model):
    objects = models.manager.Manager()
    category = models.ForeignKey(Category, verbose_name="Категория", related_name="category_for_product", blank=True,
                                 on_delete=models.CASCADE)
    name = models.CharField(verbose_name="Название продукта", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-name']
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

class ProductInfo(models.Model):
    objects = models.manager.Manager()
    model = models.CharField(verbose_name='Модель', max_length=80, blank=True)
    external_id = models.PositiveIntegerField(verbose_name='Внешний ИД')
    product = models.ForeignKey(Product, verbose_name="Продукт", related_name="product_for_product_info", blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name="Магазин", related_name="shop_for_product_info", blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.PositiveIntegerField(verbose_name="Цена")
    price_rrc = models.PositiveIntegerField(verbose_name="Рекомендуемая цена")

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = "Информация о продукте"
        verbose_name_plural = "Информация о продуктах"
        constraints = [models.UniqueConstraint(fields=['product', 'shop', 'external_id'], name='unique_product_info')]

class Parameter(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(verbose_name="Название параметра", max_length=50, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-name']
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры"

class ProductParameter(models.Model):
    objects = models.manager.Manager()
    product_info = models.ForeignKey(ProductInfo, verbose_name="Информация о продукте",
                                     related_name="product_info_for_product_parameter", blank=True, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name="Параметр", related_name="parameter_for_product_parameter",
                                  blank=True, on_delete=models.CASCADE)
    value = models.CharField(verbose_name="Значение параметра", max_length=50)

    def __str__(self):
        return self.parameter.name

    class Meta:
        ordering = ['parameter']
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры"
        constraints = [models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')]

class ContactInfo(models.Model):
    objects = models.manager.Manager()
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", related_name='user_for_contact_info', blank=True,
                             on_delete=models.CASCADE)
    city = models.CharField(verbose_name='Город', max_length=50)
    street = models.CharField(verbose_name='Улица', max_length=100)
    house_number = models.CharField(verbose_name='№ дома', max_length=15, blank=True)
    structure = models.CharField(verbose_name='Корпус', max_length=15, blank=True)
    building = models.CharField(verbose_name='Строение',max_length=15, blank=True)
    apartment = models.CharField(verbose_name='Квартира', max_length=15, blank=True)
    phone = models.CharField(verbose_name='Телефон', max_length=20)

    def __str__(self):
        return f'{self.city} {self.street} {self.house_number} {self.phone}'

    class Meta:
        ordering = ['user']
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"

class Order(models.Model):
    objects = models.manager.Manager()
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", related_name='user_for_order', blank=True,
                             on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Статус', choices=STATE_CHOICES, max_length=15)
    contact = models.ForeignKey(ContactInfo, verbose_name='Контакт', related_name='contact_for_order', blank=True,
                                null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.dt} {self.contact}'

    class Meta:
        ordering = ['-dt']
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

class OrderItem(models.Model):
    objects = models.manager.Manager()
    order = models.ForeignKey(Order, verbose_name="Заказ", related_name='order_for_order_items', blank=True,
                              on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, verbose_name="Информация о продукте",
                                     related_name='product_info_for_order_item',blank=True, null=True,
                                     on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    def __str__(self):
        return f'{self.order} {self.product_info}'

    class Meta:
        ordering = ['-order']
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
        constraints = [models.UniqueConstraint(fields=['order', 'product_info'], name='unique_order_item')]

class ConfirmEmailToken(models.Model):
    objects = models.manager.Manager()
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", related_name='user_for_confirm_email_token',
                             blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="Когда создан токен", auto_now_add=True)
    key = models.CharField(verbose_name="Key", max_length=64, db_index=True, unique=True)

    def __str__(self):
        return 'Токен сброса пароля для пользователя {user}'.format(user=self.user)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def set_expiry(self, seconds):
        """Для установки срока действия для этого токена."""
        self.expires = self.created_at + timedelta(seconds=seconds)

class UserProfile(models.Model):
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", related_name='user_for_user_profile',
                             blank=True, on_delete=models.CASCADE)
    avatar = ThumbnailerImageField(upload_to='avatars/', blank=True, null=True)

    def save(self, *args, **kwargs):
        super(UserProfile, self).save(*args, **kwargs)
        if self.avatar:
            create_thumbnail_for_user_avatar.delay(self.user.id, UserProfile)

    def __str__(self):
        return self.user.username

class ProductProfile(models.Model):
    name = models.CharField(max_length=100)
    image = ThumbnailerImageField(upload_to='products/', blank=True, null=True)

    def save(self, *args, **kwargs):
        super(ProductProfile, self).save(*args, **kwargs)
        if self.image:
            create_thumbnail_for_product.delay(self.id, ProductProfile)

    def __str__(self):
        return self.name
