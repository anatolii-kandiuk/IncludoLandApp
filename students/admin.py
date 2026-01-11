from django.contrib import admin

from .models import AudioStory, NatureSound, StudentGameResult, StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'stars', 'created_at')
    search_fields = ('user__username', 'user__email')


@admin.register(AudioStory)
class AudioStoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    search_fields = ('title',)
    list_filter = ('is_active',)


@admin.register(NatureSound)
class NatureSoundAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'created_at')
    search_fields = ('title',)
    list_filter = ('category', 'is_active')


@admin.register(StudentGameResult)
class StudentGameResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'game_name', 'score', 'played_at')
    list_filter = ('game_key',)
    search_fields = ('student__user__username', 'game_name', 'game_key')
