from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('api/game-results/', views.record_game_result, name='record_game_result'),
    path('api/story-listens/', views.record_story_listen, name='record_story_listen'),
    path('api/my-stories/', views.record_my_story, name='record_my_story'),
    path('api/predict-performance/', views.predict_performance, name='predict_performance'),
    path('rewards/', views.rewards_entry, name='rewards'),
    path('profile/', views.child_profile, name='child_profile'),
    path('specialist/', views.specialist_profile, name='specialist_profile'),

    path('specialist/sounds/', views.specialist_sounds, name='specialist_sounds'),
    path('specialist/sounds/<int:card_id>/edit/', views.specialist_sound_edit, name='specialist_sound_edit'),
    path('specialist/sounds/<int:card_id>/delete/', views.specialist_sound_delete, name='specialist_sound_delete'),

    path('specialist/stories/', views.specialist_stories, name='specialist_stories'),
    path('specialist/stories/<int:story_id>/edit/', views.specialist_story_edit, name='specialist_story_edit'),
    path('specialist/stories/<int:story_id>/delete/', views.specialist_story_delete, name='specialist_story_delete'),

    path('specialist/words/', views.specialist_words, name='specialist_words'),
    path('specialist/words/<int:word_id>/delete/', views.specialist_word_delete, name='specialist_word_delete'),

    path('specialist/sentences/', views.specialist_sentences, name='specialist_sentences'),
    path('specialist/sentences/<int:exercise_id>/delete/', views.specialist_sentence_delete, name='specialist_sentence_delete'),

    path('specialist/articulation/', views.specialist_articulation, name='specialist_articulation'),
    path('specialist/articulation/<int:card_id>/delete/', views.specialist_articulation_delete, name='specialist_articulation_delete'),

    path('specialist/my-story/', views.specialist_my_story, name='specialist_my_story'),
    path('specialist/my-story/<int:image_id>/delete/', views.specialist_my_story_delete, name='specialist_my_story_delete'),

    path('specialist/activities/', views.specialist_activity_builder, name='specialist_activity_builder'),
    path('specialist/activities/<int:activity_id>/delete/', views.specialist_activity_delete, name='specialist_activity_delete'),
    path('specialist/activities/steps/<int:step_id>/delete/', views.specialist_activity_step_delete, name='specialist_activity_step_delete'),

    path('specialist/coloring/', views.specialist_coloring_pages, name='specialist_coloring_pages'),
    path('specialist/coloring/<int:page_id>/delete/', views.specialist_coloring_page_delete, name='specialist_coloring_page_delete'),

    path('specialist/print/', views.specialist_print, name='specialist_print'),
    path('specialist/print/math/', views.specialist_print_math, name='specialist_print_math'),
    path('specialist/print/sentences/', views.specialist_print_sentences, name='specialist_print_sentences'),
    path('specialist/print/words/', views.specialist_print_words, name='specialist_print_words'),
    path('specialist/print/attention/', views.specialist_print_attention, name='specialist_print_attention'),
    path('specialist/print/memory/', views.specialist_print_memory, name='specialist_print_memory'),

    # Public print (available for all authenticated users)
    path('print/', views.print_hub, name='print_hub'),
    path('print/math/', views.print_math, name='print_math'),
    path('print/sentences/', views.print_sentences, name='print_sentences'),
    path('print/words/', views.print_words, name='print_words'),
    path('print/attention/', views.print_attention, name='print_attention'),
    path('print/memory/', views.print_memory, name='print_memory'),

    path('specialist/students/add/', views.specialist_add_student, name='specialist_add_student'),
    path('specialist/students/<int:child_profile_id>/', views.specialist_student_stats, name='specialist_student_stats'),
    path('specialist/students/<int:child_profile_id>/notes/', views.specialist_student_notes, name='specialist_student_notes'),
    path('specialist/notes/<int:note_id>/delete/', views.specialist_student_note_delete, name='specialist_student_note_delete'),
    path('specialist/students/<int:child_profile_id>/remove/', views.specialist_remove_student, name='specialist_remove_student'),

    path('login/', views.RoleAwareLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Registration (child only). Keep the legacy /register/ route.
    path('register/', views.register_child, name='register'),
    path('register/child/', views.register_child, name='register_child'),
]
