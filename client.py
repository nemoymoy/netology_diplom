import requests

# Создание пользователя

print("Создание пользователя админа")
data = requests.post(url="http://127.0.0.1:1337/api/v1/user/register",
                     json={
                            "email": "nemoymoy@yandex.ru",
                            "password": "Aa12345678!",
                            "company": "Example Inc",
                            "position": "Manager",
                            "username": "django",
                            "first_name": "John",
                            "last_name": "Doe",
                            "is_active": True,
                            "type": "buyer",
                     }
)
print(data.status_code)
