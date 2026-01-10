from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    special_needs = models.TextField(default='', blank=True)
    level = models.PositiveSmallIntegerField(default=1)
    stars = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Stats are shown only in the student profile (for registered children)
    last_exercise_type = models.ForeignKey(
        'exercises.ExerciseType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    last_score = models.PositiveSmallIntegerField(default=0)
    last_correct = models.PositiveSmallIntegerField(default=0)
    last_total = models.PositiveSmallIntegerField(default=0)
    last_completed_at = models.DateTimeField(null=True, blank=True)


    def __str__(self) -> str:
        return f"{self.user.username} (child)"
