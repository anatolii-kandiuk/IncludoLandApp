from django.db import models


class ExerciseBlock(models.Model):
    """Main learning block (Math, Language, Logic, etc.)"""
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-book')
    color = models.CharField(max_length=20, default='primary')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ExerciseType(models.Model):
    """Type of exercise within a block (Addition, Subtraction, etc.)"""
    block = models.ForeignKey(ExerciseBlock, on_delete=models.CASCADE, related_name='exercise_types')
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120)
    description = models.TextField(blank=True)
    difficulty = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['block', 'slug']

    def __str__(self):
        return f"{self.block.name} - {self.name}"


class Question(models.Model):
    """Individual question in a quiz"""
    exercise_type = models.ForeignKey(ExerciseType, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    correct_answer = models.CharField(max_length=255)
    options = models.JSONField(default=list, blank=True)  # For multiple choice
    image = models.ImageField(upload_to='questions/images/', blank=True, null=True)
    audio = models.FileField(upload_to='questions/audio/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


# Keep old models for backward compatibility, mark as deprecated
class ExerciseCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Exercise(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey(ExerciseCategory, on_delete=models.SET_NULL, null=True, related_name='exercises')
    content = models.JSONField(default=dict, blank=True)
    difficulty = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    image = models.ImageField(upload_to='exercises/images/', blank=True, null=True)
    audio = models.FileField(upload_to='exercises/audio/', blank=True, null=True)

    def __str__(self):
        return self.title
