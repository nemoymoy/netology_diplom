from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import (
    CustomUser,
    Shop,
    Category,
    Product,
    ProductInfo,
    Parameter,
    ProductParameter,
    Order,
    OrderItem,
    ContactInfo,
    ConfirmEmailToken,
)

# Register your models here.


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    add_fieldsets = (
        (None, {"fields": ("username", "email", "password", "type")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "company", "position")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    fieldsets = (
        (None, {"fields": ("username", "email", "password", "type")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "company", "position")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    list_display = [
        "id",
        "email",
        "username",
        "type",
        "first_name",
        "last_name",
        "company",
        "position",
        "is_staff",
        "is_active",
        "is_superuser",
    ]
    ordering = ("email",)
    list_filter = ("is_active", "is_staff", "is_superuser")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_active=True)

    def is_staff_display(self, obj):
        return "Yes" if obj.is_staff else "No"

    is_staff_display.short_description = "Is Staff"


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    model = Shop
    fieldsets = (
        (None, {"fields": ("name", "status")}),
        ("Additional Info", {"fields": ("url", "user")}),
    )
    list_display = ("id", "name", "url", "status")
    search_fields = ["name"]
    list_filter = ("status",)
    list_editable = ("status",)


class ProductInline(admin.TabularInline):
    model = Product
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    model = Category
    inlines = [ProductInline]
    list_display = (
        "id",
        "name",
    )
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category")
    search_fields = ("name", "category")


class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 1


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    model = ProductInfo
    fieldsets = (
        (None, {"fields": ("product", "model", "external_id", "quantity", "shop")}),
        ("Цены", {"fields": ("price", "price_rrc")}),
    )
    list_display = (
        "id",
        "product",
        "model",
        "external_id",
        "price",
        "price_rrc",
        "quantity",
        "shop",
    )
    search_fields = ["product__name"]
    list_filter = (
        "model",
        "product",
    )
    inlines = [ProductParameterInline]


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )
    search_fields = ["name"]


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ("id", "product_info", "parameter", "value")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    model = Order
    fields = ("user", "status", "contact", "dt")
    list_display = ("id", "user", "dt", "status", "contact")
    search_fields = ["user__email"]
    list_filter = ("status",)
    readonly_fields = ("dt",)
    inlines = [
        OrderItemInline,
    ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product_info", "quantity")


@admin.register(ContactInfo)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "city",
        "street",
        "house_number",
        "structure",
        "building",
        "apartment",
        "phone",
    )
    search_fields = ["city", "phone"]


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "key",
        "created_at",
    )
    search_fields = ["user__email"]
    list_filter = ("created_at",)
