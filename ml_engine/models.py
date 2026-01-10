from django.db import models


class StudentAnalytics(models.Model):
	student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='analytics')
	data = models.JSONField(default=dict, blank=True)  # aggregated metrics
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Analytics for {self.student.user.username}"


class Recommendation(models.Model):
	student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='recommendations')
	exercise = models.ForeignKey('exercises.Exercise', on_delete=models.SET_NULL, null=True, blank=True)
	reason = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Recommendation for {self.student.user.username}"

