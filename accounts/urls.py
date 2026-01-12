from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('rewards/', views.rewards_entry, name='rewards'),
    path('profile/', views.child_profile, name='child_profile'),

    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
]
