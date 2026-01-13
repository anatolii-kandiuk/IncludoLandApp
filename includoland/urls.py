from django.contrib import admin
from django.urls import path

from django.urls import include

from .views import coming_soon, game_attention, game_math, game_memory, game_sounds, games, home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', home, name='home'),
    path('games/', games, name='games'),
    path('games/words/', lambda r: coming_soon(r, 'Пазли слів'), name='game_words'),
    path('games/memory/', game_memory, name='game_memory'),
    path('games/attention/', game_attention, name='game_attention'),
    path('games/math/', game_math, name='game_math'),
    path('stories/', lambda r: coming_soon(r, 'Казки'), name='stories'),
    path('sounds/', game_sounds, name='sounds'),
    # /rewards/ handled by accounts.urls (auth-gated)
]
