from django.db import models
from django.conf import settings
from exercises.models import Exercise, ExerciseType


class StudentProgress(models.Model):
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='progress')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='progress', null=True, blank=True)
    exercise_type = models.ForeignKey(ExerciseType, on_delete=models.CASCADE, related_name='progress', null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    correct = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    time_spent = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0.0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.exercise_type:
            return f"{self.student.user.username} - {self.exercise_type.name} ({self.score}%)"
        return f"{self.student.user.username} - {self.exercise.title if self.exercise else 'Unknown'} ({self.score})"
