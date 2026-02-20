from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.deconstruct import deconstructible

import uuid
from pathlib import Path


@deconstructible
class UniqueUploadTo:
    def __init__(self, prefix: str):
        self.prefix = prefix.strip('/')

    def __call__(self, _instance, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        return f"{self.prefix}/{uuid.uuid4().hex}{suffix}"


class ChildProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='child_profile')
    stars = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"ChildProfile({self.user.username})"

    class Meta:
        verbose_name = 'Профіль дитини'
        verbose_name_plural = 'Профілі дітей'


class SpecialistProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='specialist_profile')
    students = models.ManyToManyField(
        'ChildProfile',
        related_name='specialists',
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"SpecialistProfile({self.user.username})"

    class Meta:
        verbose_name = 'Профіль спеціаліста'
        verbose_name_plural = 'Профілі спеціалістів'


class SpecialistInvite(models.Model):
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_specialist_invites',
    )
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_specialist_invites',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Запрошення спеціаліста'
        verbose_name_plural = 'Запрошення спеціалістів'

    def __str__(self) -> str:
        return f"SpecialistInvite({self.email}, {self.token})"

    def is_valid(self) -> bool:
        if self.used_at:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True


class GameResult(models.Model):
    class GameType(models.TextChoices):
        MATH = 'math', 'Math'
        MEMORY = 'memory', 'Memory'
        ATTENTION = 'attention', 'Attention'
        SOUND = 'sound', 'Sound'
        WORDS = 'words', 'Words'
        SENTENCES = 'sentences', 'Sentences'
        ARTICULATION = 'articulation', 'Articulation'

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
    max_streak = models.PositiveIntegerField(null=True, blank=True)

    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Результат гри'
        verbose_name_plural = 'Результати ігор'

    def __str__(self) -> str:
        return f"GameResult({self.user.username}, {self.game_type}, {self.score})"


class SoundCard(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sound_cards',
    )

    title = models.CharField(max_length=80)
    image = models.ImageField(upload_to=UniqueUploadTo('sounds/images'))
    audio = models.FileField(upload_to=UniqueUploadTo('sounds/audio'))

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Картка звуку'
        verbose_name_plural = 'Картки звуків'

    def __str__(self) -> str:
        return f"SoundCard({self.title})"


class ArticulationCard(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articulation_cards',
    )

    title = models.CharField(max_length=80)
    instruction = models.TextField(blank=True)
    image = models.ImageField(upload_to=UniqueUploadTo('articulation/images'))
    sounds = models.CharField(max_length=120, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Артикуляційна вправа'
        verbose_name_plural = 'Артикуляційні вправи'

    def __str__(self) -> str:
        return f"ArticulationCard({self.title})"


class ArticulationCardImage(models.Model):
    card = models.ForeignKey(
        ArticulationCard,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to=UniqueUploadTo('articulation/images'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Зображення для артикуляції'
        verbose_name_plural = 'Зображення для артикуляції'

    def __str__(self) -> str:
        return f"ArticulationCardImage({self.card_id})"


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

    image = models.ImageField(upload_to=UniqueUploadTo('stories/images'), blank=True, null=True)

    text = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to=UniqueUploadTo('stories/pdf'), blank=True, null=True)
    audio = models.FileField(upload_to=UniqueUploadTo('stories/audio'), blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Казка'
        verbose_name_plural = 'Казки'

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
        verbose_name = 'Прослуховування казки'
        verbose_name_plural = 'Прослуховування казок'

    def __str__(self) -> str:
        return f"StoryListen({self.user.username}, {self.story_id})"


class MyStoryImage(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='my_story_images',
    )

    title = models.CharField(max_length=120)
    image = models.ImageField(upload_to=UniqueUploadTo('my_story/images'))

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Зображення для історії'
        verbose_name_plural = 'Зображення для історій'

    def __str__(self) -> str:
        return f"MyStoryImage({self.title})"


class MyStoryEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='my_story_entries',
    )
    image = models.ForeignKey(
        MyStoryImage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entries',
    )

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Моя історія'
        verbose_name_plural = 'Мої історії'

    def __str__(self) -> str:
        return f"MyStoryEntry({self.user.username}, {self.id})"


class SpecialistActivity(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='specialist_activities',
    )

    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Сценарій активності'
        verbose_name_plural = 'Сценарії активностей'

    def __str__(self) -> str:
        return f"SpecialistActivity({self.title})"


class SpecialistActivityStep(models.Model):
    activity = models.ForeignKey(
        SpecialistActivity,
        on_delete=models.CASCADE,
        related_name='steps',
    )

    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    task_text = models.CharField(max_length=220)
    image = models.ImageField(upload_to=UniqueUploadTo('activities/images'))
    audio = models.FileField(upload_to=UniqueUploadTo('activities/audio'), blank=True, null=True)

    position = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'created_at']
        verbose_name = 'Крок активності'
        verbose_name_plural = 'Кроки активності'

    def __str__(self) -> str:
        return f"SpecialistActivityStep({self.activity_id}, {self.position})"


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
        verbose_name = 'Нагорода'
        verbose_name_plural = 'Нагороди'

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
        verbose_name = 'Слово пазлу'
        verbose_name_plural = 'Слова пазлів'

    def __str__(self) -> str:
        return f"WordPuzzleWord({self.word})"


class SentenceExercise(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sentence_exercises',
    )

    prompt = models.CharField(max_length=140)
    sentence = models.CharField(max_length=220)
    emoji = models.CharField(max_length=8, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Вправа з реченнями'
        verbose_name_plural = 'Вправи з реченнями'

    def __str__(self) -> str:
        return f"SentenceExercise({self.prompt})"


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
        verbose_name = 'Нотатка спеціаліста'
        verbose_name_plural = 'Нотатки спеціаліста'

    def __str__(self) -> str:
        return f"SpecialistStudentNote({self.specialist.user.username} → {self.student.user.username})"


class ColoringPage(models.Model):
    class FileType(models.TextChoices):
        IMAGE = 'image', 'Image'
        PDF = 'pdf', 'PDF'

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coloring_pages',
    )

    title = models.CharField(max_length=120)
    file = models.FileField(upload_to=UniqueUploadTo('coloring/pages'))
    file_type = models.CharField(max_length=8, choices=FileType.choices, default=FileType.IMAGE)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Розмальовка'
        verbose_name_plural = 'Розмальовки'

    def __str__(self) -> str:
        return f"ColoringPage({self.title})"
