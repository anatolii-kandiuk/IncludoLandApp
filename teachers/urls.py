from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_edit, name='profile_edit'),
    path('children/add/', views.add_child, name='add_child'),
    path('create-block/', views.create_exercise_block, name='create_block'),
    path('create-type/', views.create_exercise_type, name='create_type'),
    path('create-question/', views.create_question, name='create_question'),
]
