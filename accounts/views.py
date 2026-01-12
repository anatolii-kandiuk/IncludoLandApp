import json

from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import RegisterForm
from .models import ChildProfile, GameResult, SpecialistProfile


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

    results = list(
        GameResult.objects.filter(user=request.user)
        .only('game_type', 'score', 'created_at')
        .order_by('created_at')
    )

    line_labels = [r.created_at.strftime('%d.%m %H:%M') for r in results]
    math_values = [r.score if r.game_type == GameResult.GameType.MATH else None for r in results]
    memory_values = [r.score if r.game_type == GameResult.GameType.MEMORY else None for r in results]

    def avg_score(game_type: str) -> int:
        values = [r.score for r in results if r.game_type == game_type]
        if not values:
            return 0
        return int(round(sum(values) / len(values)))

    math_avg = avg_score(GameResult.GameType.MATH)
    memory_avg = avg_score(GameResult.GameType.MEMORY)

    progress = [
        {'label': 'Математика', 'value': math_avg},
        {'label': "Памʼять", 'value': memory_avg},
    ]

    radar_labels = ['Математика', "Памʼять"]
    radar_values = [math_avg, memory_avg]

    line_datasets = [
        {'label': 'Математика', 'data': math_values, 'color': '#2b97e5'},
        {'label': "Памʼять", 'data': memory_values, 'color': '#19b3b9'},
    ]

    context = {
        'username': request.user.username,
        'stars': profile.stars,
        'rewards': rewards,
        'progress': progress,
        'line_labels': json.dumps(line_labels, ensure_ascii=False),
        'line_datasets': json.dumps(line_datasets, ensure_ascii=False),
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


@login_required
@require_POST
def record_game_result(request):
    if hasattr(request.user, 'specialist_profile'):
        return JsonResponse({'ok': False, 'error': 'specialist_cannot_record'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)

    game_type = payload.get('game_type')
    if game_type not in (GameResult.GameType.MATH, GameResult.GameType.MEMORY):
        return JsonResponse({'ok': False, 'error': 'invalid_game_type'}, status=400)

    def to_int(value, *, min_value=None, max_value=None):
        if value is None:
            return None
        try:
            iv = int(value)
        except (TypeError, ValueError):
            return None
        if min_value is not None and iv < min_value:
            return None
        if max_value is not None and iv > max_value:
            return None
        return iv

    score = to_int(payload.get('score'), min_value=0, max_value=100)
    if score is None:
        return JsonResponse({'ok': False, 'error': 'invalid_score'}, status=400)

    raw_score = to_int(payload.get('raw_score'), min_value=0)
    max_score = to_int(payload.get('max_score'), min_value=0)
    duration_seconds = to_int(payload.get('duration_seconds'), min_value=0)

    details = payload.get('details')
    if details is None:
        details = {}
    if not isinstance(details, dict):
        return JsonResponse({'ok': False, 'error': 'invalid_details'}, status=400)

    result = GameResult.objects.create(
        user=request.user,
        game_type=game_type,
        score=score,
        raw_score=raw_score,
        max_score=max_score,
        duration_seconds=duration_seconds,
        details=details,
    )

    return JsonResponse({'ok': True, 'id': result.id})
