from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from django.urls import include

from .views import (
    coming_soon,
    game_attention,
    game_articulation,
    game_math,
    game_memory,
    game_sentences,
    game_sounds,
    game_words,
    games,
    home,
    learn_alphabet,
    learn_alphabet_print,
    learn_coloring,
    learn_coloring_print,
    learn_colors,
    learn_colors_print,
    learn_numbers,
    learn_numbers_print,
    stories_library,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', home, name='home'),
    path('games/', games, name='games'),
    path('games/words/', game_words, name='game_words'),
    path('games/sentences/', game_sentences, name='game_sentences'),
    path('games/memory/', game_memory, name='game_memory'),
    path('games/attention/', game_attention, name='game_attention'),
    path('games/math/', game_math, name='game_math'),
    path('games/articulation/', game_articulation, name='game_articulation'),
    path('stories/', stories_library, name='stories'),
    path('sounds/', game_sounds, name='sounds'),
    path('learn/alphabet/', learn_alphabet, name='learn_alphabet'),
    path('learn/alphabet/print/', learn_alphabet_print, name='learn_alphabet_print'),
    path('learn/numbers/', learn_numbers, name='learn_numbers'),
    path('learn/numbers/print/', learn_numbers_print, name='learn_numbers_print'),
    path('learn/colors/', learn_colors, name='learn_colors'),
    path('learn/colors/print/', learn_colors_print, name='learn_colors_print'),
    path('learn/coloring/', learn_coloring, name='learn_coloring'),
    path('learn/coloring/print/', learn_coloring_print, name='learn_coloring_print'),
    path('soon/<str:section>/', coming_soon, name='coming_soon'),
    # /rewards/ handled by accounts.urls (auth-gated)
]

if settings.DEBUG and settings.MEDIA_ROOT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
