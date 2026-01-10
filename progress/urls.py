from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-stats/', views.admin_stats, name='admin_stats'),
    path('admin-stats/export/', views.export_stats_csv, name='export_stats_csv'),
    path('admin-stats/export-pdf/', views.export_stats_pdf, name='export_stats_pdf'),
    path('admin-stats/student/<str:username>/', views.student_detail, name='student_detail'),
]
