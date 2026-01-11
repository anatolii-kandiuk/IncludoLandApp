from django.urls import path

from . import views

app_name = 'students'

urlpatterns = [
	path('profile/', views.profile, name='profile'),
	path('dashboard/', views.dashboard, name='dashboard'),
	path('games/', views.games, name='games'),
	path('games/finish/', views.game_finish, name='game_finish'),
	path('games/memory/', views.game_memory, name='game_memory'),
	path('games/attention/', views.game_attention, name='game_attention'),
	path('games/speech/', views.game_speech, name='game_speech'),
	path('games/math/', views.game_math, name='game_math'),
	path('rewards/', views.rewards, name='rewards'),
	path('audiostories/', views.audiostories, name='audiostories'),
	path('nature-sounds/', views.nature_sounds, name='nature_sounds'),
]
