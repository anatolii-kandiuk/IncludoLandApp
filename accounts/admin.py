from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin.sites import NotRegistered
from django.core.mail import send_mail
from django.utils import timezone

from .models import (
    ChildProfile,
    ColoringPage,
    GameResult,
    SentenceExercise,
    SoundCard,
    SpecialistInvite,
    SpecialistProfile,
    SpecialistStudentNote,
    Story,
    StoryListen,
    UserBadge,
    WordPuzzleWord,
)


User = get_user_model()

try:
    admin.site.unregister(User)
except NotRegistered:
    pass


class ChildProfileInline(admin.StackedInline):
    model = ChildProfile
    extra = 0
    can_delete = True


class SpecialistProfileInline(admin.StackedInline):
    model = SpecialistProfile
    extra = 0
    can_delete = True
    filter_horizontal = ('students',)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = (ChildProfileInline, SpecialistProfileInline)
    list_display = DjangoUserAdmin.list_display + ('is_staff', 'is_superuser', 'is_active')
    list_filter = DjangoUserAdmin.list_filter + ('is_staff', 'is_superuser', 'is_active')


@admin.register(SpecialistInvite)
class SpecialistInviteAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'token',
        'created_at',
        'expires_at',
        'used_at',
        'used_by',
    )
    list_filter = ('used_at',)
    search_fields = ('email', 'token')
    readonly_fields = ('token', 'created_at', 'used_at', 'used_by')
    actions = ['send_invite_email', 'expire_selected']

    @admin.action(description='Send invite email')
    def send_invite_email(self, request, queryset):
        sent = 0
        failed = 0

        for inv in queryset:
            if not inv.email:
                failed += 1
                continue

            invite_url = request.build_absolute_uri(f"/register/specialist/?invite={inv.token}")
            subject = 'Запрошення для реєстрації спеціаліста — IncludoLand'
            body = (
                'Вітаємо!\n\n'
                'Вас запросили зареєструватися як спеціаліст у IncludoLand.\n'
                'Перейдіть за посиланням (одноразове):\n'
                f"{invite_url}\n\n"
                'Якщо ви не очікували цього листа — просто проігноруйте його.\n'
            )

            try:
                send_mail(subject, body, None, [inv.email], fail_silently=False)
                sent += 1
            except Exception:
                failed += 1

        if sent:
            self.message_user(request, f"Sent {sent} invite(s).", level=messages.SUCCESS)
        if failed:
            self.message_user(
                request,
                f"Failed to send {failed} invite(s). Check email settings.",
                level=messages.WARNING,
            )

    @admin.action(description='Expire selected invites now')
    def expire_selected(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(expires_at=now)
        self.message_user(request, f"Expired {updated} invite(s).", level=messages.SUCCESS)


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'stars', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    list_select_related = ('user',)


@admin.register(SpecialistProfile)
class SpecialistProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'coins', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    list_select_related = ('user',)
    filter_horizontal = ('students',)


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'game_type', 'score', 'created_at')
    list_filter = ('game_type',)
    search_fields = ('user__username', 'user__email')
    list_select_related = ('user',)


@admin.register(SoundCard)
class SoundCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'created_by__username', 'created_by__email')
    list_select_related = ('created_by',)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'content_type', 'is_active', 'created_at', 'updated_at')
    list_filter = ('content_type', 'is_active')
    search_fields = ('title', 'created_by__username', 'created_by__email')
    list_select_related = ('created_by',)


@admin.register(StoryListen)
class StoryListenAdmin(admin.ModelAdmin):
    list_display = ('user', 'story', 'duration_seconds', 'created_at')
    search_fields = ('user__username', 'user__email', 'story__title')
    list_select_related = ('user', 'story')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')
    search_fields = ('user__username', 'user__email', 'code')
    list_select_related = ('user',)


@admin.register(WordPuzzleWord)
class WordPuzzleWordAdmin(admin.ModelAdmin):
    list_display = ('word', 'emoji', 'created_by', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('word', 'hint', 'created_by__username', 'created_by__email')
    list_select_related = ('created_by',)


@admin.register(SentenceExercise)
class SentenceExerciseAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'emoji', 'created_by', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('prompt', 'sentence', 'created_by__username', 'created_by__email')
    list_select_related = ('created_by',)


@admin.register(SpecialistStudentNote)
class SpecialistStudentNoteAdmin(admin.ModelAdmin):
    list_display = ('specialist', 'student', 'created_at', 'updated_at')
    search_fields = (
        'specialist__user__username',
        'specialist__user__email',
        'student__user__username',
        'student__user__email',
        'text',
    )
    list_select_related = ('specialist__user', 'student__user')


@admin.register(ColoringPage)
class ColoringPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'created_by', 'is_active', 'created_at')
    list_filter = ('file_type', 'is_active')
    search_fields = ('title', 'created_by__username', 'created_by__email')
    list_select_related = ('created_by',)
