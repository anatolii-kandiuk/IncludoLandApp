from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import ChildRegisterForm, SpecialistRegisterForm, UserLoginForm
from django.contrib.auth.views import LoginView



def register_view(request):
    # Generic registration form (keeps backward compatibility)
    return redirect('users:register_student')


def register_student(request):
    # Registration view specifically for students (children)
    if request.method == 'POST':
        form = ChildRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Реєстрація учня пройшла успішно.')
            return redirect('students:profile')
    else:
        form = ChildRegisterForm()
    return render(request, 'registration/register_student.html', {'form': form})


def register_teacher(request):
    # Registration view specifically for specialists / teachers
    if request.method == 'POST':
        form = SpecialistRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Реєстрація вчителя пройшла успішно.')
            return redirect('/')
    else:
        form = SpecialistRegisterForm()
    return render(request, 'registration/register_teacher.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = UserLoginForm

    def get_success_url(self):
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated and hasattr(user, 'student_profile'):
            return '/students/profile/'
        return super().get_success_url()
