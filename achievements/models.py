from django.db import models


class Achievement(models.Model):
	code = models.CharField(max_length=80, unique=True)
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	icon = models.ImageField(upload_to='achievements/icons/', blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.title


class StudentAchievement(models.Model):
	achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
	student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='achievements')
	awarded_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('achievement', 'student')

	def __str__(self):
		return f"{self.student.user.username} - {self.achievement.title}"


class Reward(models.Model):
	name = models.CharField(max_length=120)
	cost = models.PositiveIntegerField(default=0)  # stars cost
	description = models.TextField(blank=True)

	def __str__(self):
		return self.name

