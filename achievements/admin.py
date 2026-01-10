from django.contrib import admin
from .models import Achievement, StudentAchievement, Reward


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'created_at')
    search_fields = ('code', 'title')


@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ('student', 'achievement', 'awarded_at')
    list_filter = ('awarded_at',)
    search_fields = ('student__user__username', 'achievement__title')


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost')
    search_fields = ('name',)

