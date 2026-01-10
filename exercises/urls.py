from django.urls import path
from . import views

app_name = 'exercises'

urlpatterns = [
    # New structure: blocks -> types -> quiz
    path('', views.block_list, name='block_list'),
    path('<slug:block_slug>/', views.exercise_type_list, name='type_list'),

    # Tasks within a type (each question is a task)
    path('<slug:block_slug>/<slug:type_slug>/tasks/', views.task_list, name='task_list'),
    path('<slug:block_slug>/<slug:type_slug>/tasks/<int:question_id>/', views.task_view, name='task_view'),
    path('<slug:block_slug>/<slug:type_slug>/tasks/<int:question_id>/submit/', views.task_submit, name='task_submit'),

    # Backward-compatible quiz routes
    path('<slug:block_slug>/<slug:type_slug>/', views.quiz_view, name='quiz'),
    path('<slug:block_slug>/<slug:type_slug>/submit/', views.quiz_submit, name='quiz_submit'),
    path('<slug:block_slug>/<slug:type_slug>/print/', views.quiz_print, name='quiz_print'),
    path('<slug:block_slug>/<slug:type_slug>/print-braille/', views.print_braille, name='print_braille'),
]
