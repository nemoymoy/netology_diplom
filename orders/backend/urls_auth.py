
from django.urls import path

from .views import index_page, home_page, login_page, register_page, logout_handler

urlpatterns = [
    path('', index_page, name='index_page'),
    path('home', home_page, name="home_page"),
    path('login', login_page, name='login_page'),
    path('register', register_page, name='register'),
    path("logout", logout_handler, name="logout"),
]
