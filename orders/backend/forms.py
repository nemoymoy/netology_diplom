from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from rest_framework.response import Response

from .models import (CustomUser, ContactInfo, Order, Shop, ProductInfo,)
from django.contrib.auth.decorators import login_required

from .serializers import ContactInfoSerializer

class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    company = forms.CharField(max_length=255, required=True)
    position = forms.CharField(max_length=255, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'company', 'position']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")


class LoginForm(forms.Form):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if not (email and password):
            raise forms.ValidationError('Требуются адрес электронной почты и пароль.')

        return cleaned_data


class UserDeleteForm(forms.Form):
    confirm_delete = forms.BooleanField(
        label="Удалить учетную запись",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=True,
        error_messages={
            "required": "Вы должны подтвердить удаление учетной записи."
        }
    )


class AccountDetailsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'password',)
        widgets = {'password': forms.PasswordInput()}

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        if password:
            try:
                validate_password(password)
            except Exception as e:
                self.add_error('password', str(e))
        return cleaned_data


class ContactForm(forms.ModelForm):
    city = forms.CharField(max_length=100, required=True)
    street = forms.CharField(max_length=200, required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = ContactInfo
        fields = ['city', 'street', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].widget.attrs.update({'placeholder': 'City'})
        self.fields['street'].widget.attrs.update({'placeholder': 'Street'})
        self.fields['phone'].widget.attrs.update({'placeholder': 'Phone'})

    def clean(self):
        cleaned_data = super().clean()
        city = cleaned_data.get('city')
        street = cleaned_data.get('street')
        phone = cleaned_data.get('phone')

        if not all([city, street, phone]):
            raise forms.ValidationError("All fields are required.")

        if len(phone) != 10 or not phone.isdigit():
            raise forms.ValidationError("Invalid phone number.")

        return cleaned_data


class ContactDeleteForm(forms.Form):
    items = forms.CharField(max_length=200, required=True)

    def clean(self):
        cleaned_data = super().clean()
        items = cleaned_data.get('items')

        if not items:
            raise forms.ValidationError("Please enter one or more contact IDs to delete.")

        try:
            list_of_ids = items.split(',')
            for id in list_of_ids:
                int(id)
        except ValueError:
            raise forms.ValidationError("Invalid contact ID format. Please use comma-separated integers.")


class ContactUpdateForm(forms.ModelForm):
    class Meta:
        model = ContactInfo
        fields = ['city', 'street', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city'].widget.attrs.update({'placeholder': 'City'})
        self.fields['street'].widget.attrs.update({'placeholder': 'Street'})
        self.fields['phone'].widget.attrs.update({'placeholder': 'Phone'})


@login_required
def contact_view(request):
    if request.method == 'GET':
        contacts = ContactInfo.objects.filter(user=request.user)
        serializer = ContactInfoSerializer(contacts, many=True)
        return render(request, 'contact_list.html', {'serializer': serializer})
    elif request.method == 'POST':
        form = ContactForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('contact_list')
        else:
            return render(request, 'contact_form.html', {'form': form})
    elif request.method == 'DELETE':
        form = ContactDeleteForm(data=request.POST)
        if form.is_valid():
            items = form.cleaned_data['items']
            deleted_count = ContactInfo.objects.filter(
                Q(user=request.user),
                id__in=[int(item.strip()) for item in items.split(',')]
            ).delete()[0]
            return Response({'Status': True, 'Удалено объектов': deleted_count})
        else:
            return Response({'Status': False, 'Errors': form.errors})
    elif request.method == 'PUT':
        form = ContactUpdateForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('contact_list')
        else:
            return render(request, 'contact_update.html', {'form': form})
    else:
        return render(request, 'contact_form.html', {'form': ContactForm()})


class ShopFormCreate(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ('name', 'url', 'status')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Введите название магазина'}),
            'url': forms.URLInput(attrs={'placeholder': 'Введите URL магазина'}),
            'status': forms.CheckboxInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        return cleaned_data


class ShopFormStatus(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ('status',)


class PriceUpdateForm(forms.ModelForm):
    email = forms.EmailField(label="Email", max_length=254)
    password = forms.CharField(widget=forms.PasswordInput(), label="Password")
    url = forms.URLField(label="URL")

    class Meta:
        model = User
        fields = ['email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class ProductInfoFilterForm(forms.Form):
    shop_id = forms.IntegerField(label='Shop ID', required=False)
    category_id = forms.IntegerField(label='Category ID', required=False)

    def clean(self):
        cleaned_data = super().clean()

        shop_id = cleaned_data.get('shop_id')
        category_id = cleaned_data.get('category_id')

        if shop_id and category_id:
            raise forms.ValidationError("Cannot specify both Shop ID and Category ID.")

        return cleaned_data


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status', 'contact')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget.attrs.update({'readonly': True})


class AddToBasketForm(forms.Form):
    product_id = forms.IntegerField(label="ID товара",
                                    widget=forms.NumberInput(attrs={'placeholder': 'Введите ID товара'}))
    quantity = forms.IntegerField(label="Количество", min_value=1,
                                  widget=forms.NumberInput(attrs={'placeholder': 'Введите количество'}))

    def clean(self):
        cleaned_data = super().clean()
        product_id = cleaned_data.get("product_id")
        quantity = cleaned_data.get("quantity")

        if product_id and quantity:
            try:
                product_info = ProductInfo.objects.get(id=product_id)
                if product_info.quantity >= quantity:
                    return cleaned_data
                else:
                    raise forms.ValidationError("Недостаточно товаров на складе")
            except ProductInfo.DoesNotExist:
                raise forms.ValidationError("Товар не найден")

        return cleaned_data


class OrderFilterForm(forms.Form):
    status = forms.ChoiceField(choices=[('basket', 'Basket'), ('in_progress', 'In Progress'), ('completed', 'Completed')])
    shop_name = forms.CharField(max_length=255, required=False)
    min_date = forms.DateField(required=False)
    max_date = forms.DateField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        shop_name = cleaned_data.get('shop_name')
        min_date = cleaned_data.get('min_date')
        max_date = cleaned_data.get('max_date')

        if status and not (shop_name or min_date or max_date):
            raise forms.ValidationError("At least one filter criteria must be selected")

        return cleaned_data