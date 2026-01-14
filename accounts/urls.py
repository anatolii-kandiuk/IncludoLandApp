from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('api/game-results/', views.record_game_result, name='record_game_result'),
    path('api/story-listens/', views.record_story_listen, name='record_story_listen'),
    path('rewards/', views.rewards_entry, name='rewards'),
    path('profile/', views.child_profile, name='child_profile'),
    path('specialist/', views.specialist_profile, name='specialist_profile'),

    path('specialist/sounds/', views.specialist_sounds, name='specialist_sounds'),
    path('specialist/sounds/<int:card_id>/edit/', views.specialist_sound_edit, name='specialist_sound_edit'),
    path('specialist/sounds/<int:card_id>/delete/', views.specialist_sound_delete, name='specialist_sound_delete'),

    path('specialist/stories/', views.specialist_stories, name='specialist_stories'),
    path('specialist/stories/<int:story_id>/edit/', views.specialist_story_edit, name='specialist_story_edit'),
    path('specialist/stories/<int:story_id>/delete/', views.specialist_story_delete, name='specialist_story_delete'),

    path('specialist/students/add/', views.specialist_add_student, name='specialist_add_student'),
    path('specialist/students/<int:child_profile_id>/', views.specialist_student_stats, name='specialist_student_stats'),
    path('specialist/students/<int:child_profile_id>/remove/', views.specialist_remove_student, name='specialist_remove_student'),

    path('login/', views.RoleAwareLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_choice, name='register'),
    path('register/child/', views.register_child, name='register_child'),
    path('register/specialist/', views.register_specialist, name='register_specialist'),
]
