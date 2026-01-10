from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


def _apply_bootstrap_classes(form: forms.Form) -> None:
    for name, field in form.fields.items():
        widget = field.widget
        existing = widget.attrs.get('class', '')
        if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
            css = 'form-check-input'
        elif isinstance(widget, forms.Select):
            css = 'form-select'
        else:
            css = 'form-control'
        widget.attrs['class'] = (existing + ' ' + css).strip()
        if name in ('username', 'email'):
            widget.attrs.setdefault('autocomplete', 'username')
        if name.startswith('password'):
            widget.attrs.setdefault('autocomplete', 'new-password')

class ChildRegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap_classes(self)

    class Meta:
        from core.models import User
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        from students.models import StudentProfile

        user = super().save(commit=False)
        user.role = 'child'
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
            StudentProfile.objects.get_or_create(
                user=user,
                defaults={'grade': '1', 'special_needs': '', 'level': 1},
            )
        return user


class SpecialistRegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=False)
    experience = forms.IntegerField(label="Досвід (років)", required=False, min_value=0, max_value=100)
    specialization = forms.CharField(label="Спеціалізація", required=False, max_length=100)
    about = forms.CharField(label="Про себе", required=False, widget=forms.Textarea)

    class Meta:
        from core.models import User
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "experience",
            "specialization",
            "about",
        ]

    def save(self, commit=True):
        from teachers.models import TeacherProfile

        user = super().save(commit=False)
        user.role = 'specialist'
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
            TeacherProfile.objects.get_or_create(
                user=user,
                defaults={
                    'experience': self.cleaned_data.get('experience'),
                    'specialization': self.cleaned_data.get('specialization', ''),
                    'about': self.cleaned_data.get('about', ''),
                },
            )
        return user

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Email або логін")
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        _apply_bootstrap_classes(self)
        self.fields['password'].widget.attrs.setdefault('autocomplete', 'current-password')
