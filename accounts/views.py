import json

from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import RegisterForm
from .models import ChildProfile, SpecialistProfile


def rewards_entry(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'specialist_profile'):
            return redirect('specialist_profile')
        return redirect('child_profile')

    return render(request, 'auth/auth_required.html', {'next': request.get_full_path()})


def register_choice(request):
    if request.user.is_authenticated:
        # Prefer specialist dashboard if specialist profile exists.
        if hasattr(request.user, 'specialist_profile'):
            return redirect('specialist_profile')
        return redirect('child_profile')

    return render(request, 'auth/register_choice.html', {'next': request.GET.get('next', '')})


def _handle_register(request, *, kind: str):
    if request.user.is_authenticated:
        if kind == 'specialist':
            return redirect('specialist_profile')
        return redirect('child_profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            if kind == 'specialist':
                SpecialistProfile.objects.get_or_create(user=user, defaults={'coins': 5320})
                redirect_default = reverse('specialist_profile')
            else:
                ChildProfile.objects.get_or_create(user=user, defaults={'stars': 0})
                redirect_default = reverse('child_profile')

            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or redirect_default)
    else:
        form = RegisterForm()

    template = 'auth/register_child.html' if kind == 'child' else 'auth/register_specialist.html'
    return render(request, template, {'form': form, 'next': request.GET.get('next', '')})


def register_child(request):
    return _handle_register(request, kind='child')


def register_specialist(request):
    return _handle_register(request, kind='specialist')


class RoleAwareLoginView(LoginView):
    template_name = 'auth/login.html'

    def get_success_url(self):
        next_url = self.get_redirect_url()
        if next_url:
            return next_url

        user = self.request.user
        if hasattr(user, 'specialist_profile'):
            return reverse('specialist_profile')
        if hasattr(user, 'child_profile'):
            return reverse('child_profile')
        return reverse('home')


@login_required
def child_profile(request):
    if hasattr(request.user, 'specialist_profile'):
        return redirect('specialist_profile')

    profile, _created = ChildProfile.objects.get_or_create(
        user=request.user,
        defaults={'stars': 1250},
    )

    rewards = [
        {'title': 'Ерудит', 'subtitle': 'Пройшов 1 блок', 'tone': 'red', 'icon': 'book'},
        {'title': 'Математик', 'subtitle': 'Вирішив 5 блоків', 'tone': 'orange', 'icon': 'calc'},
        {'title': 'Дослідник', 'subtitle': 'Вивчив 8 блоків', 'tone': 'green', 'icon': 'compass'},
        {'title': 'Увага', 'subtitle': '5 ігор', 'tone': 'teal', 'icon': 'target'},
    ]

    progress = [
        {'label': 'Пазли слів', 'value': 75},
        {'label': "Памʼять", 'value': 50},
        {'label': 'Увага', 'value': 30},
    ]

    line_labels = ['0', '1', '2', '3', '4', '5', '6']
    line_values = [0, 8, 22, 45, 62, 78, 92]

    radar_labels = ['Математика', "Памʼять", 'Пазли', 'Увага']
    radar_values = [55, 72, 40, 60]

    context = {
        'username': request.user.username,
        'stars': profile.stars,
        'rewards': rewards,
        'progress': progress,
        'line_labels': json.dumps(line_labels, ensure_ascii=False),
        'line_values': json.dumps(line_values),
        'radar_labels': json.dumps(radar_labels, ensure_ascii=False),
        'radar_values': json.dumps(radar_values),
    }
    return render(request, 'profile/child_profile.html', context)


@login_required
def specialist_profile(request):
    # NOTE: No classes are stored in DB by request; this page uses mock data only.

    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    specialist = request.user.specialist_profile

    attention_students = [
        {
            'name': 'Іван І.',
            'subtitle': 'Зосередженість: Памʼять',
            'progress': 35,
        },
        {
            'name': 'Іван І.',
            'subtitle': 'Зосередженість: Памʼять',
            'progress': 70,
        },
    ]

    activity_labels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
    activity_yellow = [20, 45, 30, 80, 55, 70, 90]
    activity_teal = [10, 25, 60, 50, 75, 40, 65]

    context = {
        'username': request.user.username,
        'coins': specialist.coins,
        'attention_students': attention_students,
        'activity_labels': json.dumps(activity_labels, ensure_ascii=False),
        'activity_yellow': json.dumps(activity_yellow),
        'activity_teal': json.dumps(activity_teal),
    }
    return render(request, 'profile/specialist_profile.html', context)
