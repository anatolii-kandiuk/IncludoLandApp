from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import SoundCard, Story


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


class StoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When editing existing story, allow keeping current files.
        if getattr(self.instance, 'pk', None):
            self.fields['image'].required = False
            self.fields['pdf_file'].required = False
            self.fields['audio'].required = False

    class Meta:
        model = Story
        fields = ('title', 'content_type', 'image', 'text', 'pdf_file', 'audio')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Назва казки'}),
            'text': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Текст казки...'}),
        }

    def clean(self):
        cleaned = super().clean()
        content_type = cleaned.get('content_type')
        text = (cleaned.get('text') or '').strip()
        pdf_file = cleaned.get('pdf_file')

        if content_type == Story.ContentType.TEXT:
            if not text:
                self.add_error('text', 'Додайте текст казки.')
        elif content_type == Story.ContentType.PDF:
            has_existing_pdf = bool(getattr(self.instance, 'pk', None) and getattr(self.instance, 'pdf_file', None))
            if not pdf_file and not has_existing_pdf:
                self.add_error('pdf_file', 'Завантажте PDF файл казки.')
        else:
            self.add_error('content_type', 'Оберіть тип контенту.')

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.content_type == Story.ContentType.TEXT:
            # Clear PDF if switching to text.
            instance.pdf_file = None
        if instance.content_type == Story.ContentType.PDF:
            # Clear text if switching to PDF.
            instance.text = ''
        if commit:
            instance.save()
        return instance
