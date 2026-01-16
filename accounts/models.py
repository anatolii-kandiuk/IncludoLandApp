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

    students = models.ManyToManyField(
        'ChildProfile',
        related_name='specialists',
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"SpecialistProfile({self.user.username})"


class GameResult(models.Model):
    class GameType(models.TextChoices):
        MATH = 'math', 'Math'
        MEMORY = 'memory', 'Memory'
        SOUND = 'sound', 'Sound'
        WORDS = 'words', 'Words'

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


class SoundCard(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sound_cards',
    )

    title = models.CharField(max_length=80)
    image = models.ImageField(upload_to='sounds/images/')
    audio = models.FileField(upload_to='sounds/audio/')

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"SoundCard({self.title})"


class Story(models.Model):
    class ContentType(models.TextChoices):
        TEXT = 'text', 'Text'
        PDF = 'pdf', 'PDF'

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stories',
    )

    title = models.CharField(max_length=120)
    content_type = models.CharField(max_length=8, choices=ContentType.choices, default=ContentType.TEXT)

    image = models.ImageField(upload_to='stories/images/', blank=True, null=True)

    text = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to='stories/pdf/', blank=True, null=True)
    audio = models.FileField(upload_to='stories/audio/', blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Story({self.title})"


class StoryListen(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='story_listens',
    )
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='listens',
    )
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"StoryListen({self.user.username}, {self.story_id})"


class UserBadge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='badges',
    )
    code = models.CharField(max_length=48)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'code'),)
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"UserBadge({self.user.username}, {self.code})"


class WordPuzzleWord(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='word_puzzle_words',
    )

    word = models.CharField(max_length=24)
    hint = models.CharField(max_length=200, blank=True)
    emoji = models.CharField(max_length=8, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"WordPuzzleWord({self.word})"


class SpecialistStudentNote(models.Model):
    specialist = models.ForeignKey(
        'SpecialistProfile',
        on_delete=models.CASCADE,
        related_name='student_notes',
    )
    student = models.ForeignKey(
        'ChildProfile',
        on_delete=models.CASCADE,
        related_name='specialist_notes',
    )

    text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"SpecialistStudentNote({self.specialist.user.username} → {self.student.user.username})"
