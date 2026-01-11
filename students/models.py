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


class AudioStory(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    audio = models.FileField(upload_to='audio/stories/')
    cover = models.ImageField(upload_to='audio/stories/covers/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title', 'id']

    def __str__(self) -> str:
        return self.title


class NatureSound(models.Model):
    CATEGORY_CHOICES = [
        ('nature', 'Природа'),
        ('city', 'Місто'),
        ('home', 'Дім'),
        ('transport', 'Транспорт'),
    ]

    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='nature')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    audio = models.FileField(upload_to='audio/sounds/')
    icon = models.CharField(max_length=60, default='bi-volume-up')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'title', 'id']

    def __str__(self) -> str:
        return self.title


class StudentGameResult(models.Model):
    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='game_results',
    )
    game_key = models.CharField(max_length=40)
    game_name = models.CharField(max_length=80)
    score = models.PositiveSmallIntegerField(default=0)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_at', '-id']
        indexes = [
            models.Index(fields=['student', 'game_key', 'played_at']),
        ]

    def __str__(self) -> str:
        return f"{self.student.user.username}: {self.game_name} = {self.score}"
