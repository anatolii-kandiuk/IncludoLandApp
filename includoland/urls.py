from django.contrib import admin
from django.urls import path

from .views import coming_soon, games, home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('games/', games, name='games'),
    path('games/words/', lambda r: coming_soon(r, 'Пазли слів'), name='game_words'),
    path('games/memory/', lambda r: coming_soon(r, "Памʼять"), name='game_memory'),
    path('games/attention/', lambda r: coming_soon(r, 'Увага'), name='game_attention'),
    path('games/math/', lambda r: coming_soon(r, 'Математика'), name='game_math'),
    path('stories/', lambda r: coming_soon(r, 'Казки'), name='stories'),
    path('sounds/', lambda r: coming_soon(r, 'Звуки'), name='sounds'),
    path('rewards/', lambda r: coming_soon(r, 'Нагороди'), name='rewards'),
]
