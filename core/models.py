from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
	"""Custom user with role (student, teacher, parent)."""
	ROLE_CHILD = 'child'
	ROLE_SPECIALIST = 'specialist'
	ROLE_PARENT = 'parent'
	ROLE_ADMIN = 'admin'

	ROLE_CHOICES = [
		(ROLE_CHILD, 'Дитина'),
		(ROLE_SPECIALIST, 'Спеціаліст'),
		(ROLE_PARENT, 'Батько/Мати'),
		(ROLE_ADMIN, 'Адмін'),
	]

	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CHILD)
	avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

	def is_child(self):
		return self.role == self.ROLE_CHILD

	def is_specialist(self):
		return self.role == self.ROLE_SPECIALIST

	def is_parent(self):
		return self.role == self.ROLE_PARENT

	def __str__(self):
		return self.get_full_name() or self.username
