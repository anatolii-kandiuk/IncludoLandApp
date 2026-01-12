from django.conf import settings
from django.db import models


class ChildProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='child_profile')
    stars = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"ChildProfile({self.user.username})"


class SpecialistProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='specialist_profile')
    coins = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"SpecialistProfile({self.user.username})"


class GameResult(models.Model):
    class GameType(models.TextChoices):
        MATH = 'math', 'Math'
        MEMORY = 'memory', 'Memory'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_results',
    )
    game_type = models.CharField(max_length=16, choices=GameType.choices)

    # Normalized score for charts and monitoring (0..100)
    score = models.PositiveSmallIntegerField(default=0)

    # Optional raw score info (e.g., correct/total for math)
    raw_score = models.PositiveIntegerField(null=True, blank=True)
    max_score = models.PositiveIntegerField(null=True, blank=True)

    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"GameResult({self.user.username}, {self.game_type}, {self.score})"
