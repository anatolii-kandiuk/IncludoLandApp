import json

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import RegisterForm
from .models import ChildProfile


def rewards_entry(request):
    if request.user.is_authenticated:
        return redirect('child_profile')

    return render(request, 'auth/auth_required.html', {'next': request.get_full_path()})


def register(request):
    if request.user.is_authenticated:
        return redirect('child_profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            ChildProfile.objects.get_or_create(user=user, defaults={'stars': 0})
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or reverse('child_profile'))
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form, 'next': request.GET.get('next', '')})


@login_required
def child_profile(request):
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
