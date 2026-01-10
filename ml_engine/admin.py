from django.contrib import admin
from .models import StudentAnalytics, Recommendation


@admin.register(StudentAnalytics)
class StudentAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('student', 'updated_at')
    search_fields = ('student__user__username',)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('student', 'exercise', 'reason', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('student__user__username', 'exercise__title')

