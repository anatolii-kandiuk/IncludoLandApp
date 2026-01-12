from django.contrib import admin
from django.urls import path

from .views import hello_world

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', hello_world, name='hello_world'),
]
