from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
    Group,
    Permission,
)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator
from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta
from easy_thumbnails.fields import ThumbnailerImageField
# from .tasks import create_thumbnail_for_avatar_user, create_thumbnail_for_avatar_product

USER_TYPE_CHOICES = (("shop", "Магазин"), ("buyer", "Покупатель"))

STATE_CHOICES = (
    ("basket", "Статус корзины"),
    ("new", "Новый"),
    ("confirmed", "Подтвержден"),
    ("assembled", "Собран"),
    ("sent", "Отправлен"),
    ("delivered", "Доставлен"),
    ("canceled", "Отменен"),
)

# Create your models here.


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name="Email", max_length=255, unique=True)
    company = models.CharField(verbose_name="Компания", max_length=40, blank=True)
    position = models.CharField(verbose_name="Должность", max_length=40, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        verbose_name="Псевдоним",
        max_length=150,
        unique=True,
        help_text=_(
            "Требования. Не более 150 символов. Только буквы, цифры и @/./+/-/_."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("Пользователь с таким именем пользователя уже существует.")
        },
    )
    first_name = models.CharField(verbose_name="Имя", max_length=30, blank=True)
    last_name = models.CharField(verbose_name="Фамилия", max_length=30, blank=True)
    is_staff = models.BooleanField(
        verbose_name="Администратор",
        default=False,
        help_text=_(
            "Определяет, может ли пользователь войти на этот сайт администратора."
        ),
    )
    is_active = models.BooleanField(
        verbose_name="Активен",
        default=False,
        help_text=_(
            "Определяет, следует ли считать этого пользователя активным."
            "Снимите этот флажок вместо удаления учетных записей."
        ),
    )
    type = models.CharField(
        verbose_name="Тип пользователя",
        choices=USER_TYPE_CHOICES,
        max_length=5,
        default="buyer",
    )
    date_joined = models.DateTimeField(
        verbose_name="Дата присоединения", default=timezone.now
    )
    group = models.ManyToManyField(
        Group, verbose_name="Группа", related_name="group_for_user", blank=True
    )
    permission = models.ManyToManyField(
        Permission,
        verbose_name="Разрешение",
        related_name="permission_for_user",
        blank=True,
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["email"]

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
    name = models.CharField(
        verbose_name="Название магазина",
        max_length=100,
        null=False,
        blank=False,
        unique=True,
    )
    url = models.URLField(verbose_name="URL магазина", null=True, blank=True)
    user = models.OneToOneField(
        CustomUser,
        verbose_name="Пользователь",
        related_name="user_for_shop",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    status = models.BooleanField(verbose_name="Статус", default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-name"]
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"


class Category(models.Model):
    objects = models.manager.Manager()
    shops = models.ManyToManyField(
        Shop, verbose_name="Магазины", related_name="categories", blank=True
    )
    name = models.CharField(verbose_name="Название категории", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Product(models.Model):
    objects = models.manager.Manager()
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        related_name="products",
        blank=True,
        on_delete=models.CASCADE,
    )
    name = models.CharField(verbose_name="Название продукта", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-name"]
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"


class ProductInfo(models.Model):
    objects = models.manager.Manager()
    model = models.CharField(verbose_name="Модель", max_length=80, blank=True)
    external_id = models.PositiveIntegerField(verbose_name="Внешний ИД")
    product = models.ForeignKey(
        Product,
        verbose_name="Продукт",
        related_name="products_info",
        blank=True,
        on_delete=models.CASCADE,
    )
    shop = models.ForeignKey(
        Shop,
        verbose_name="Магазин",
        related_name="products_info",
        blank=True,
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.PositiveIntegerField(verbose_name="Цена")
    price_rrc = models.PositiveIntegerField(verbose_name="Рекомендуемая цена")

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = "Информация о продукте"
        verbose_name_plural = "Информация о продуктах"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "shop", "external_id"], name="unique_product_info"
            )
        ]


class Parameter(models.Model):
    objects = models.manager.Manager()
    name = models.CharField(
        verbose_name="Название параметра", max_length=50, blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-name"]
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры"


class ProductParameter(models.Model):
    objects = models.manager.Manager()
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name="Информация о продукте",
        related_name="product_parameters",
        blank=True,
        on_delete=models.CASCADE,
    )
    parameter = models.ForeignKey(
        Parameter,
        verbose_name="Параметр",
        related_name="product_parameters",
        blank=True,
        on_delete=models.CASCADE,
    )
    value = models.CharField(verbose_name="Значение параметра", max_length=50)

    def __str__(self):
        return self.parameter.name

    class Meta:
        ordering = ["parameter"]
        verbose_name = "Параметр продукта"
        verbose_name_plural = "Параметры продукта"
        constraints = [
            models.UniqueConstraint(
                fields=["product_info", "parameter"], name="unique_product_parameter"
            )
        ]


class ContactInfo(models.Model):
    objects = models.manager.Manager()
    user = models.ForeignKey(
        CustomUser,
        verbose_name="Пользователь",
        related_name="contacts",
        blank=True,
        on_delete=models.CASCADE,
    )
    city = models.CharField(verbose_name="Город", max_length=50)
    street = models.CharField(verbose_name="Улица", max_length=100)
    house_number = models.CharField(verbose_name="№ дома", max_length=15, blank=True)
    structure = models.CharField(verbose_name="Корпус", max_length=15, blank=True)
    building = models.CharField(verbose_name="Строение", max_length=15, blank=True)
    apartment = models.CharField(verbose_name="Квартира", max_length=15, blank=True)
    phone = models.CharField(verbose_name="Телефон", max_length=20)

    def __str__(self):
        return f"{self.city} {self.street} {self.house_number} {self.phone}"

    class Meta:
        ordering = ["user"]
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"


class Order(models.Model):
    objects = models.manager.Manager()
    user = models.ForeignKey(
        CustomUser,
        verbose_name="Пользователь",
        related_name="orders",
        blank=True,
        on_delete=models.CASCADE,
    )
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        verbose_name="Статус", choices=STATE_CHOICES, max_length=15
    )
    contact = models.ForeignKey(
        ContactInfo,
        verbose_name="Контакт",
        related_name="contact_for_order",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.user} {self.dt}"

    class Meta:
        ordering = ["-dt"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    objects = models.manager.Manager()
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        related_name="ordered_items",
        blank=True,
        on_delete=models.CASCADE,
    )
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name="Информация о продукте",
        related_name="ordered_items",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    shop = models.ForeignKey(
        Shop,
        verbose_name="Магазин",
        related_name="order_items",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    def __str__(self):
        return f"{self.order} {self.product_info}"

    class Meta:
        ordering = ["-order"]
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
        constraints = [
            models.UniqueConstraint(
                fields=["order_id", "product_info"], name="unique_order_item"
            )
        ]


class ConfirmEmailToken(models.Model):
    objects = models.manager.Manager()
    user = models.ForeignKey(
        CustomUser,
        verbose_name="Пользователь",
        related_name="confirm_email_tokens",
        blank=True,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(
        verbose_name="Когда создан токен", auto_now_add=True
    )
    key = models.CharField(
        verbose_name="Key", max_length=64, db_index=True, unique=True
    )

    def __str__(self):
        return "Токен сброса пароля для пользователя {user}".format(user=self.user)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Токен подтверждения Email"
        verbose_name_plural = "Токены подтверждения Email"

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


class AvatarUser(models.Model):
    objects = models.manager.Manager()
    user = models.OneToOneField(
        CustomUser,
        verbose_name="Пользователь",
        related_name="avatar_user",
        on_delete=models.CASCADE
    )
    title = models.CharField(
        verbose_name="Имя файла",
        max_length=100,
        blank=True,
        null=True
    )
    image = ThumbnailerImageField(
        verbose_name="Аватар",
        upload_to="images_user/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.title, self.user.username

    class Meta:
        ordering = ["user"]
        verbose_name = "Аватар Пользователя"
        verbose_name_plural = "Аватары Пользователей"
        constraints = [
            models.UniqueConstraint(fields=["user"], name="unique_avatar")
        ]

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.user.username
        super(AvatarUser, self).save(*args, **kwargs)
        # if self.image:
        #     create_thumbnail_for_avatar_user(user_id=self.user.id)


class AvatarProduct(models.Model):
    objects = models.manager.Manager()
    product = models.OneToOneField(
        Product,
        verbose_name="Продукт",
        related_name="avatar_product",
        on_delete=models.CASCADE
    )
    title = models.CharField(
        verbose_name="Имя файла",
        max_length=100,
        blank=True,
        null=True
    )
    image = ThumbnailerImageField(
        verbose_name="Изображение",
        upload_to="images_product/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.title, self.product.name

    class Meta:
        ordering = ["product"]
        verbose_name = "Изображение продукта"
        verbose_name_plural = "Изображения продуктов"
        constraints = [
            models.UniqueConstraint(fields=["product"], name="unique_image")
        ]

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.product.name
        super(AvatarProduct, self).save(*args, **kwargs)
        # if self.image:
        #     create_thumbnail_for_avatar_product(product_id=self.product.id)