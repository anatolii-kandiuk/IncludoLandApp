from django import forms

from .models import StudentProfile


class StudentProfileSpecialNeedsForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['special_needs']
        labels = {
            'special_needs': "Особливі потреби (необов'язково)",
        }
        widgets = {
            'special_needs': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()
            field.widget.attrs.setdefault('placeholder', 'Наприклад: потрібні більші кнопки, повільніший темп, підказки…')
