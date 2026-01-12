from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('rewards/', views.rewards_entry, name='rewards'),
    path('profile/', views.child_profile, name='child_profile'),
    path('specialist/', views.specialist_profile, name='specialist_profile'),

    path('login/', views.RoleAwareLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_choice, name='register'),
    path('register/child/', views.register_child, name='register_child'),
    path('register/specialist/', views.register_specialist, name='register_specialist'),
]
