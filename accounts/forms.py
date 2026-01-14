from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import SoundCard


class RegisterForm(UserCreationForm):
    username = forms.CharField(label='Логін', max_length=150)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')


class SoundCardForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When editing existing card, allow keeping current files.
        if getattr(self.instance, 'pk', None):
            self.fields['image'].required = False
            self.fields['audio'].required = False

    class Meta:
        model = SoundCard
        fields = ('title', 'image', 'audio')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Підпис до картинки'}),
        }
