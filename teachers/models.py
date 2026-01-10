from django.db import models
from django.conf import settings

class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    experience = models.PositiveSmallIntegerField("Досвід (років)", null=True, blank=True)
    specialization = models.CharField("Спеціалізація", max_length=100, blank=True)
    about = models.TextField("Про себе", blank=True)
    # Teachers can have multiple students assigned to them
    students = models.ManyToManyField('students.StudentProfile', blank=True, related_name='teachers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} (teacher)"
