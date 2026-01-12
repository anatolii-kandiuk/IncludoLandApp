from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    username = forms.CharField(label='Логін', max_length=150)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
