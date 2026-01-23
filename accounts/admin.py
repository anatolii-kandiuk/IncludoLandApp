from django.contrib import admin, messages
from django.core.mail import send_mail
from django.utils import timezone

from .models import SpecialistInvite


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
