from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from .models import (
    ArticulationCard,
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


admin.site.site_header = 'IncludoLand'
admin.site.site_title = 'IncludoLand Admin'
admin.site.index_title = 'Панель керування'


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
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff_label', 'is_superuser_label', 'is_active_label')
    list_filter = DjangoUserAdmin.list_filter + ('is_staff', 'is_superuser', 'is_active')

    @admin.display(boolean=True, description='Доступ до адмінки')
    def is_staff_label(self, obj):
        return obj.is_staff

    @admin.display(boolean=True, description='Суперкористувач')
    def is_superuser_label(self, obj):
        return obj.is_superuser

    @admin.display(boolean=True, description='Активний')
    def is_active_label(self, obj):
        return obj.is_active

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active'),
        }),
    )


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
    class CreateSpecialistForm(forms.ModelForm):
        username = forms.CharField(label='Логін (username)', max_length=150)
        email = forms.EmailField(label='Email', required=False)
        first_name = forms.CharField(label="Ім'я", max_length=150)
        last_name = forms.CharField(label='Прізвище', max_length=150)
        password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
        password2 = forms.CharField(label='Повторіть пароль', widget=forms.PasswordInput)

        class Meta:
            model = SpecialistProfile
            fields = ()

        def clean(self):
            cleaned = super().clean()
            username = (cleaned.get('username') or '').strip()
            password1 = cleaned.get('password1')
            password2 = cleaned.get('password2')

            if not username:
                self.add_error('username', 'Введіть логін.')
            elif User.objects.filter(username=username).exists():
                self.add_error('username', 'Цей логін вже зайнятий.')

            if password1 and password2 and password1 != password2:
                raise forms.ValidationError('Паролі не співпадають.')

            if password1:
                validate_password(password1)

            return cleaned

    class ChangeSpecialistForm(forms.ModelForm):
        username = forms.CharField(label='Логін (username)', max_length=150)
        email = forms.EmailField(label='Email', required=False)
        first_name = forms.CharField(label="Ім'я", max_length=150, required=False)
        last_name = forms.CharField(label='Прізвище', max_length=150, required=False)
        password1 = forms.CharField(label='Новий пароль', widget=forms.PasswordInput, required=False)
        password2 = forms.CharField(label='Повторіть пароль', widget=forms.PasswordInput, required=False)

        class Meta:
            model = SpecialistProfile
            fields = ('students',)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            user = getattr(self.instance, 'user', None)
            if user is not None:
                self.fields['username'].initial = user.username
                self.fields['email'].initial = user.email
                self.fields['first_name'].initial = user.first_name
                self.fields['last_name'].initial = user.last_name

        def clean(self):
            cleaned = super().clean()

            user = getattr(self.instance, 'user', None)
            username = (cleaned.get('username') or '').strip()
            if not username:
                self.add_error('username', 'Введіть логін.')
            else:
                qs = User.objects.filter(username=username)
                if user is not None:
                    qs = qs.exclude(pk=user.pk)
                if qs.exists():
                    self.add_error('username', 'Цей логін вже зайнятий.')

            password1 = cleaned.get('password1')
            password2 = cleaned.get('password2')
            if password1 or password2:
                if password1 != password2:
                    raise forms.ValidationError('Паролі не співпадають.')
                validate_password(password1)

            return cleaned

    list_display = ('username', 'email', 'first_name', 'last_name', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    list_select_related = ('user',)
    filter_horizontal = ('students',)

    @admin.display(ordering='user__username', description='Username')
    def username(self, obj: SpecialistProfile) -> str:
        return obj.user.username

    @admin.display(ordering='user__email', description='Email')
    def email(self, obj: SpecialistProfile) -> str:
        return obj.user.email

    @admin.display(ordering='user__first_name', description='First name')
    def first_name(self, obj: SpecialistProfile) -> str:
        return obj.user.first_name

    @admin.display(ordering='user__last_name', description='Last name')
    def last_name(self, obj: SpecialistProfile) -> str:
        return obj.user.last_name

    def get_form(self, request: HttpRequest, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.CreateSpecialistForm
        else:
            kwargs['form'] = self.ChangeSpecialistForm
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request: HttpRequest, obj=None):
        if obj is None:
            return (
                (
                    'Створення спеціаліста',
                    {
                        'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
                    },
                ),
            )

        return (
            (
                'Профіль спеціаліста',
                {
                    'fields': ('user', 'username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'students'),
                },
            ),
        )

    def get_readonly_fields(self, request: HttpRequest, obj=None):
        if obj is None:
            return ()
        return ('user',)

    @transaction.atomic
    def save_model(self, request: HttpRequest, obj: SpecialistProfile, form, change: bool) -> None:
        if not change:
            username = form.cleaned_data['username'].strip()
            first_name = form.cleaned_data['first_name'].strip()
            last_name = form.cleaned_data['last_name'].strip()
            password = form.cleaned_data['password1']

            user = User.objects.create(
                username=username,
                email=form.cleaned_data.get('email') or '',
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            user.set_password(password)
            user.save(update_fields=['password'])

            obj.user = user

            self.message_user(
                request,
                f"Створено спеціаліста. Логін для входу: {username}",
                level=messages.SUCCESS,
            )

        else:
            user = obj.user
            user.username = form.cleaned_data['username'].strip()
            user.email = (form.cleaned_data.get('email') or '').strip()
            user.first_name = (form.cleaned_data.get('first_name') or '').strip()
            user.last_name = (form.cleaned_data.get('last_name') or '').strip()

            password1 = form.cleaned_data.get('password1')
            if password1:
                user.set_password(password1)
                user.save(update_fields=['username', 'email', 'first_name', 'last_name', 'password'])
            else:
                user.save(update_fields=['username', 'email', 'first_name', 'last_name'])

        super().save_model(request, obj, form, change)


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


@admin.register(ArticulationCard)
class ArticulationCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'instruction', 'created_by__username', 'created_by__email')
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
