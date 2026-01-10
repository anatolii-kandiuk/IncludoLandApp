from django.contrib import admin
from .models import StudentProgress


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'exercise', 'score', 'completed', 'created_at')
    list_filter = ('completed', 'created_at')
    search_fields = ('student__user__username', 'exercise__title')

