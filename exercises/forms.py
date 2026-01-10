from django import forms
import json

from .models import ExerciseBlock, ExerciseType, Question

class ExerciseBlockForm(forms.ModelForm):
    class Meta:
        model = ExerciseBlock
        fields = ['name', 'slug', 'description', 'icon', 'color', 'order']

class ExerciseTypeForm(forms.ModelForm):
    class Meta:
        model = ExerciseType
        fields = ['block', 'name', 'slug', 'description', 'difficulty', 'order', 'is_active']


class QuestionForm(forms.ModelForm):
    options_text = forms.CharField(
        label='Варіанти відповіді',
        required=False,
        widget=forms.Textarea,
        help_text='Введіть варіанти (кожен з нового рядка). Якщо порожньо — будуть згенеровані автоматично.',
    )

    class Meta:
        model = Question
        fields = ['exercise_type', 'question_text', 'correct_answer', 'image', 'audio', 'order']

    def clean(self):
        cleaned = super().clean()
        raw = (self.data.get('options_text') or '').strip()
        if raw:
            options = [line.strip() for line in raw.splitlines() if line.strip()]
            cleaned['options'] = options
        else:
            cleaned['options'] = []
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.options = self.cleaned_data.get('options', [])
        if commit:
            instance.save()
        return instance
