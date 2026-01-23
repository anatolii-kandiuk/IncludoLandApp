from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ColoringPage, SentenceExercise, SoundCard, SpecialistStudentNote, Story, WordPuzzleWord


class RegisterForm(UserCreationForm):
    username = forms.CharField(label='Логін', max_length=150)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')


class SpecialistRegisterForm(UserCreationForm):
    username = forms.CharField(label='Логін', max_length=150)
    email = forms.EmailField(label='Email')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


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


class WordPuzzleWordForm(forms.ModelForm):
    class Meta:
        model = WordPuzzleWord
        fields = ('word', 'hint', 'emoji', 'is_active')
        widgets = {
            'word': forms.TextInput(attrs={'placeholder': 'Слово (наприклад: КІТ)'}),
            'hint': forms.TextInput(attrs={'placeholder': 'Підказка (необовʼязково)'}),
            'emoji': forms.TextInput(attrs={'placeholder': 'Емодзі (необовʼязково)'}),
        }

    def clean_word(self):
        value = (self.cleaned_data.get('word') or '').strip()
        value = value.replace(' ', '')
        value = value.upper()
        if not value:
            raise forms.ValidationError('Введіть слово.')

        allowed = set('АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ')
        if any(ch not in allowed for ch in value):
            raise forms.ValidationError('Слово має містити лише українські літери без пробілів.')

        if len(value) < 2:
            raise forms.ValidationError('Слово повинно мати щонайменше 2 літери.')
        if len(value) > 24:
            raise forms.ValidationError('Слово надто довге (макс. 24 літери).')

        return value


class SpecialistStudentNoteForm(forms.ModelForm):
    class Meta:
        model = SpecialistStudentNote
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Додайте нотатку про учня...'}),
        }

    def clean_text(self):
        value = (self.cleaned_data.get('text') or '').strip()
        if not value:
            raise forms.ValidationError('Введіть текст нотатки.')
        if len(value) > 2000:
            raise forms.ValidationError('Нотатка надто довга (макс. 2000 символів).')
        return value


class SentenceExerciseForm(forms.ModelForm):
    class Meta:
        model = SentenceExercise
        fields = ('prompt', 'sentence', 'emoji', 'is_active')
        widgets = {
            'prompt': forms.TextInput(attrs={'placeholder': 'Напр.: Склади речення про котика'}),
            'sentence': forms.TextInput(attrs={'placeholder': 'Напр.: Кіт спить на дивані.'}),
            'emoji': forms.TextInput(attrs={'placeholder': 'Емодзі (необовʼязково)'}),
        }

    def clean_prompt(self):
        value = (self.cleaned_data.get('prompt') or '').strip()
        if not value:
            raise forms.ValidationError('Введіть підказку/тему.')
        if len(value) > 140:
            raise forms.ValidationError('Підказка надто довга (макс. 140 символів).')
        return value

    def clean_sentence(self):
        value = (self.cleaned_data.get('sentence') or '').strip()
        if not value:
            raise forms.ValidationError('Введіть речення.')
        if len(value) > 220:
            raise forms.ValidationError('Речення надто довге (макс. 220 символів).')

        # Require at least 2 words.
        words = [w for w in value.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ').split() if w]
        if len(words) < 2:
            raise forms.ValidationError('Речення має містити щонайменше 2 слова.')

        return value


class ColoringPageForm(forms.ModelForm):
    class Meta:
        model = ColoringPage
        fields = ('title', 'file', 'is_active')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Назва розмальовки'}),
        }

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if not f:
            raise forms.ValidationError('Оберіть файл.')

        name = (getattr(f, 'name', '') or '').lower()
        allowed = ('.pdf', '.png', '.jpg', '.jpeg')
        if not any(name.endswith(ext) for ext in allowed):
            raise forms.ValidationError('Підтримуються лише PDF, PNG, JPG/JPEG.')

        size = getattr(f, 'size', 0) or 0
        if size > 12 * 1024 * 1024:
            raise forms.ValidationError('Файл завеликий (макс. 12 MB).')

        return f

    def save(self, commit=True):
        instance = super().save(commit=False)
        name = (getattr(instance.file, 'name', '') or '').lower()
        if name.endswith('.pdf'):
            instance.file_type = ColoringPage.FileType.PDF
        else:
            instance.file_type = ColoringPage.FileType.IMAGE

        if commit:
            instance.save()
        return instance
