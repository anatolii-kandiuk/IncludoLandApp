import json
from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render
from django.db.models import Avg, Q
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone
from django.db.models import F

import random

from .forms import RegisterForm, ColoringPageForm, SentenceExerciseForm, SoundCardForm, SpecialistStudentNoteForm, StoryForm, WordPuzzleWordForm
from .models import ChildProfile, ColoringPage, GameResult, SentenceExercise, SoundCard, SpecialistStudentNote, Story, StoryListen, UserBadge, WordPuzzleWord


BADGE_DEFINITIONS = [
    {
        'code': 'first_game',
        'title': 'Старт',
        'subtitle': 'Перша зіграна гра',
        'tone': 'red',
        'icon': 'target',
    },
    {
        'code': 'math_5',
        'title': 'Математик',
        'subtitle': '5 ігор з математики',
        'tone': 'orange',
        'icon': 'calc',
    },
    {
        'code': 'memory_5',
        'title': "Памʼять",
        'subtitle': '5 ігор на памʼять',
        'tone': 'teal',
        'icon': 'compass',
    },
    {
        'code': 'words_5',
        'title': 'Слова',
        'subtitle': '5 ігор зі словами',
        'tone': 'green',
        'icon': 'book',
    },
    {
        'code': 'sound_5',
        'title': 'Слухач',
        'subtitle': '5 ігор зі звуками',
        'tone': 'yellow',
        'icon': 'target',
    },
    {
        'code': 'stories_3',
        'title': 'Казкар',
        'subtitle': 'Прослухав 3 різні казки',
        'tone': 'blue',
        'icon': 'book',
    },
    {
        'code': 'sentences_5',
        'title': 'Будівничий речень',
        'subtitle': '5 ігор з реченнями',
        'tone': 'purple',
        'icon': 'book',
    },
    {
        'code': 'math_20',
        'title': 'Супер математик',
        'subtitle': '20 ігор з математики',
        'tone': 'orange',
        'icon': 'calc',
    },
    {
        'code': 'memory_20',
        'title': 'Мега памʼять',
        'subtitle': '20 ігор на памʼять',
        'tone': 'teal',
        'icon': 'compass',
    },
    {
        'code': 'words_20',
        'title': 'Майстер слів',
        'subtitle': '20 ігор зі словами',
        'tone': 'green',
        'icon': 'book',
    },
    {
        'code': 'sound_20',
        'title': 'Майстер звуків',
        'subtitle': '20 ігор зі звуками',
        'tone': 'yellow',
        'icon': 'target',
    },
    {
        'code': 'stories_10',
        'title': 'Книжковий герой',
        'subtitle': 'Прослухав 10 різних казок',
        'tone': 'blue',
        'icon': 'book',
    },
    {
        'code': 'all_games_25',
        'title': 'Чемпіон',
        'subtitle': '25 зіграних ігор',
        'tone': 'red',
        'icon': 'target',
    },
]


def _badge_codes_for_user(user):
    return set(UserBadge.objects.filter(user=user).values_list('code', flat=True))


def _award_badge(user, code: str) -> bool:
    if not code:
        return False
    _obj, created = UserBadge.objects.get_or_create(user=user, code=code)
    return created


def _sync_badges_for_user(user) -> None:
    total_results = GameResult.objects.filter(user=user).count()
    if total_results >= 1:
        _award_badge(user, 'first_game')
    if total_results >= 25:
        _award_badge(user, 'all_games_25')

    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.MATH).count() >= 5:
        _award_badge(user, 'math_5')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.MATH).count() >= 20:
        _award_badge(user, 'math_20')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.MEMORY).count() >= 5:
        _award_badge(user, 'memory_5')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.MEMORY).count() >= 20:
        _award_badge(user, 'memory_20')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.WORDS).count() >= 5:
        _award_badge(user, 'words_5')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.WORDS).count() >= 20:
        _award_badge(user, 'words_20')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.SOUND).count() >= 5:
        _award_badge(user, 'sound_5')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.SOUND).count() >= 20:
        _award_badge(user, 'sound_20')

    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.SENTENCES).count() >= 5:
        _award_badge(user, 'sentences_5')

    listened_unique = (
        StoryListen.objects.filter(user=user)
        .values('story_id')
        .distinct()
        .count()
    )
    if listened_unique >= 3:
        _award_badge(user, 'stories_3')
    if listened_unique >= 10:
        _award_badge(user, 'stories_10')


def _build_rewards_for_user(user):
    unlocked = _badge_codes_for_user(user)
    rewards = []
    for d in BADGE_DEFINITIONS:
        rewards.append(
            {
                'code': d['code'],
                'title': d['title'],
                'subtitle': d['subtitle'],
                'tone': d['tone'],
                'icon': d['icon'],
                'unlocked': d['code'] in unlocked,
            }
        )
    return rewards


def _build_child_stats_for_user(user):
    results = list(
        GameResult.objects.filter(user=user)
        .only('game_type', 'score', 'created_at')
        .order_by('created_at')
    )

    line_labels = [r.created_at.strftime('%d.%m %H:%M') for r in results]
    math_values = [r.score if r.game_type == GameResult.GameType.MATH else None for r in results]
    memory_values = [r.score if r.game_type == GameResult.GameType.MEMORY else None for r in results]
    sound_values = [r.score if r.game_type == GameResult.GameType.SOUND else None for r in results]
    words_values = [r.score if r.game_type == GameResult.GameType.WORDS else None for r in results]
    sentences_values = [r.score if r.game_type == GameResult.GameType.SENTENCES else None for r in results]

    def avg_score(game_type: str) -> int:
        values = [r.score for r in results if r.game_type == game_type]
        if not values:
            return 0
        return int(round(sum(values) / len(values)))

    math_avg = avg_score(GameResult.GameType.MATH)
    memory_avg = avg_score(GameResult.GameType.MEMORY)
    sound_avg = avg_score(GameResult.GameType.SOUND)
    words_avg = avg_score(GameResult.GameType.WORDS)
    sentences_avg = avg_score(GameResult.GameType.SENTENCES)

    total_stories = Story.objects.filter(is_active=True).count()
    listened_unique = (
        StoryListen.objects.filter(user=user)
        .values('story_id')
        .distinct()
        .count()
    )
    stories_listen_pct = int(round((listened_unique * 100) / total_stories)) if total_stories else 0

    progress = [
        {'label': 'Математика', 'value': math_avg},
        {'label': "Памʼять", 'value': memory_avg},
        {'label': 'Звуки', 'value': sound_avg},
        {'label': 'Пазли слів', 'value': words_avg},
        {'label': 'Побудова речень', 'value': sentences_avg},
        {'label': 'Казки (слухання)', 'value': stories_listen_pct},
    ]

    radar_labels = ['Математика', "Памʼять", 'Звуки', 'Пазли слів', 'Речення', 'Казки']
    radar_values = [math_avg, memory_avg, sound_avg, words_avg, sentences_avg, stories_listen_pct]

    line_datasets = [
        {'label': 'Математика', 'data': math_values, 'color': '#2b97e5'},
        {'label': "Памʼять", 'data': memory_values, 'color': '#19b3b9'},
        {'label': 'Звуки', 'data': sound_values, 'color': '#c28b00'},
        {'label': 'Пазли слів', 'data': words_values, 'color': '#7c3aed'},
        {'label': 'Побудова речень', 'data': sentences_values, 'color': '#8b5cf6'},
    ]

    return {
        'results_count': len(results),
        'stories_listens_count': StoryListen.objects.filter(user=user).count(),
        'stories_listened_unique': listened_unique,
        'stories_total': total_stories,
        'progress': progress,
        'line_labels': json.dumps(line_labels, ensure_ascii=False),
        'line_datasets': json.dumps(line_datasets, ensure_ascii=False),
        'radar_labels': json.dumps(radar_labels, ensure_ascii=False),
        'radar_values': json.dumps(radar_values),
        'avg': {
            'math': math_avg,
            'memory': memory_avg,
            'sound': sound_avg,
            'words': words_avg,
            'sentences': sentences_avg,
            'stories_listen': stories_listen_pct,
        },
    }


def rewards_entry(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'specialist_profile'):
            return redirect('specialist_profile')
        profile, _created = ChildProfile.objects.get_or_create(user=request.user, defaults={'stars': 0})
        _sync_badges_for_user(request.user)
        rewards = _build_rewards_for_user(request.user)
        unlocked_count = sum(1 for r in rewards if r['unlocked'])
        context = {
            'username': request.user.username,
            'stars': profile.stars,
            'rewards': rewards,
            'unlocked_count': unlocked_count,
            'total_count': len(rewards),
        }
        return render(request, 'profile/rewards.html', context)

    return render(request, 'auth/auth_required.html', {'next': request.get_full_path()})


def _handle_child_register(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'specialist_profile'):
            return redirect('specialist_profile')
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

    return render(request, 'auth/register_child.html', {'form': form, 'next': request.GET.get('next', '')})


def register_child(request):
    return _handle_child_register(request)


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
        defaults={'stars': 0},
    )

    _sync_badges_for_user(request.user)
    rewards = _build_rewards_for_user(request.user)

    rewards_unlocked = [r for r in rewards if r.get('unlocked')]
    rewards_locked = [r for r in rewards if not r.get('unlocked')]

    stats = _build_child_stats_for_user(request.user)

    context = {
        'username': request.user.username,
        'stars': profile.stars,
        'rewards': rewards,
        'rewards_unlocked': rewards_unlocked,
        'rewards_locked': rewards_locked,
        'progress': stats['progress'],
        'line_labels': stats['line_labels'],
        'line_datasets': stats['line_datasets'],
        'radar_labels': stats['radar_labels'],
        'radar_values': stats['radar_values'],
        'stories_listens_count': stats['stories_listens_count'],
        'stories_listened_unique': stats['stories_listened_unique'],
        'stories_total': stats['stories_total'],
    }
    return render(request, 'profile/child_profile.html', context)


@login_required
def specialist_profile(request):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    specialist = request.user.specialist_profile

    q = (request.GET.get('q') or '').strip()
    my_students = list(
        specialist.students.select_related('user')
        .order_by('user__username')
    )

    my_ids = {s.id for s in my_students}

    search_results = []
    if q:
        search_results = list(
            ChildProfile.objects.select_related('user')
            .filter(
                Q(user__username__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
            )
            .exclude(id__in=my_ids)
            .order_by('user__username')[:20]
        )

    def _focus_from_stats(stats_dict: dict):
        avg = stats_dict.get('avg') or {}
        candidates = [
            ('Математика', int(avg.get('math') or 0)),
            ("Памʼять", int(avg.get('memory') or 0)),
            ('Звуки', int(avg.get('sound') or 0)),
            ('Пазли слів', int(avg.get('words') or 0)),
            ('Побудова речень', int(avg.get('sentences') or 0)),
        ]
        label, value = min(candidates, key=lambda x: x[1])
        severity = max(0, min(100, 100 - int(value)))
        return label, int(value), severity

    attention_students = []
    for s in my_students[:6]:
        stats = _build_child_stats_for_user(s.user)
        focus_label, _focus_value, focus_severity = _focus_from_stats(stats)
        attention_students.append(
            {
                'id': s.id,
                'name': s.user.username,
                'subtitle': f'Зосередженість: {focus_label}',
                'progress': focus_severity,
            }
        )

    student_cards = []
    for s in my_students[:50]:
        stats = _build_child_stats_for_user(s.user)
        focus_label, _focus_value, focus_severity = _focus_from_stats(stats)
        student_cards.append(
            {
                'id': s.id,
                'name': s.user.username,
                'subtitle': f'Зосередженість: {focus_label}',
                'progress': focus_severity,
                'stars': s.stars,
            }
        )

    activity_labels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
    activity_yellow = [20, 45, 30, 80, 55, 70, 90]
    activity_teal = [10, 25, 60, 50, 75, 40, 65]

    # Performance chart filters (specialist dashboard)
    perf_child_raw = (request.GET.get('perf_child') or 'all').strip()
    perf_game_raw = (request.GET.get('perf_game') or 'all').strip()
    perf_days_raw = (request.GET.get('perf_days') or '14').strip()

    try:
        perf_days = int(perf_days_raw)
    except ValueError:
        perf_days = 14
    if perf_days not in (7, 14, 30, 90):
        perf_days = 14

    allowed_game_types = {c[0] for c in GameResult.GameType.choices}
    perf_game = perf_game_raw if perf_game_raw in allowed_game_types else 'all'

    selected_child = None
    if perf_child_raw != 'all':
        try:
            perf_child_id = int(perf_child_raw)
        except ValueError:
            perf_child_id = None
        if perf_child_id is not None:
            selected_child = next((s for s in my_students if s.id == perf_child_id), None)

    today = timezone.localdate()
    start_date = today - timedelta(days=perf_days - 1)

    user_ids = [selected_child.user_id] if selected_child else [s.user_id for s in my_students]
    perf_labels = []
    perf_datasets = []

    if user_ids:
        day_list = [start_date + timedelta(days=i) for i in range(perf_days)]
        perf_labels = [d.strftime('%d.%m') for d in day_list]

        base_qs = GameResult.objects.filter(
            user_id__in=user_ids,
            created_at__date__gte=start_date,
            created_at__date__lte=today,
        )

        def build_series(game_type: str) -> list:
            rows = (
                base_qs.filter(game_type=game_type)
                .annotate(day=TruncDate('created_at'))
                .values('day')
                .annotate(avg=Avg('score'))
                .order_by('day')
            )
            by_day = {r['day']: int(round(r['avg'] or 0)) for r in rows}
            return [by_day.get(d) for d in day_list]

        game_palette = {
            GameResult.GameType.MATH: '#2b97e5',
            GameResult.GameType.MEMORY: '#19b3b9',
            GameResult.GameType.SOUND: '#c28b00',
            GameResult.GameType.WORDS: '#7c3aed',
            GameResult.GameType.SENTENCES: '#8b5cf6',
        }
        game_labels = {
            GameResult.GameType.MATH: 'Математика',
            GameResult.GameType.MEMORY: "Памʼять",
            GameResult.GameType.SOUND: 'Звуки',
            GameResult.GameType.WORDS: 'Пазли слів',
            GameResult.GameType.SENTENCES: 'Побудова речень',
        }

        if perf_game == 'all':
            for gt in (GameResult.GameType.MATH, GameResult.GameType.MEMORY, GameResult.GameType.SOUND, GameResult.GameType.WORDS, GameResult.GameType.SENTENCES):
                perf_datasets.append({'label': game_labels[gt], 'data': build_series(gt), 'color': game_palette[gt]})
        else:
            perf_datasets.append({'label': game_labels.get(perf_game, perf_game), 'data': build_series(perf_game), 'color': game_palette.get(perf_game, '#2b97e5')})

    context = {
        'username': request.user.username,
        'coins': specialist.coins,
        'attention_students': attention_students,
        'my_students': my_students,
        'student_cards': student_cards,
        'q': q,
        'search_results': search_results,
        'activity_labels': json.dumps(activity_labels, ensure_ascii=False),
        'activity_yellow': json.dumps(activity_yellow),
        'activity_teal': json.dumps(activity_teal),
        'perf_labels': json.dumps(perf_labels, ensure_ascii=False),
        'perf_datasets': json.dumps(perf_datasets, ensure_ascii=False),
        'perf_days': perf_days,
        'perf_game': perf_game,
        'perf_child': selected_child.id if selected_child else 'all',
        'perf_game_choices': list(GameResult.GameType.choices),
    }
    return render(request, 'profile/specialist_profile.html', context)


@login_required
def specialist_sentences(request):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    if request.method == 'POST':
        form = SentenceExerciseForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()
            return redirect('specialist_sentences')
    else:
        form = SentenceExerciseForm(initial={'is_active': True})

    exercises = list(
        SentenceExercise.objects.filter(created_by=request.user)
        .only('id', 'prompt', 'sentence', 'emoji', 'is_active', 'created_at')
        .order_by('-created_at')
    )

    context = {
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'form': form,
        'exercises': exercises,
    }
    return render(request, 'profile/specialist_sentences.html', context)


@login_required
@require_POST
def specialist_sentence_delete(request, exercise_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    SentenceExercise.objects.filter(id=exercise_id, created_by=request.user).delete()
    next_url = request.POST.get('next') or reverse('specialist_sentences')
    return redirect(next_url)


def _require_specialist(request):
    if not hasattr(request.user, 'specialist_profile'):
        return False
    return True


UKR_ALPHABET = 'АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ'


def _parse_choice(request, name: str, allowed: set, default: str) -> str:
    value = (request.GET.get(name) or '').strip()
    return value if value in allowed else default


def _shuffle_with_rng(rng: random.Random, items: list):
    a = list(items)
    rng.shuffle(a)
    return a


def _math_allowed_ops_for_level(level: str) -> set:
    if level == 'hard':
        return {'mul', 'div'}
    return {'add', 'sub'}


def _math_op_symbol(op: str) -> str:
    if op == 'add':
        return '+'
    if op == 'sub':
        return '−'
    if op == 'mul':
        return '×'
    if op == 'div':
        return '÷'
    return '?'


def _math_rand_int(rng: random.Random, min_v: int, max_v: int) -> int:
    return rng.randint(min_v, max_v)


def _generate_math_items(rng: random.Random, level: str, op_mode: str, total: int = 10):
    allowed_set = _math_allowed_ops_for_level(level)

    def pick(arr):
        return arr[_math_rand_int(rng, 0, len(arr) - 1)]

    items = []
    for i in range(total):
        if op_mode == 'mix':
            op = pick(sorted(list(allowed_set)))
        else:
            op = op_mode if op_mode in allowed_set else pick(sorted(list(allowed_set)))

        if level == 'easy':
            a = _math_rand_int(rng, 0, 9)
            b = _math_rand_int(rng, 0, 9)
            if op == 'sub' and b > a:
                a, b = b, a
        elif level == 'medium':
            a = _math_rand_int(rng, 10, 100)
            b = _math_rand_int(rng, 10, 100)
            if op == 'sub' and b > a:
                a, b = b, a
        else:
            # hard
            if op == 'div':
                divisor = _math_rand_int(rng, 2, 12)
                quotient = _math_rand_int(rng, 2, 12)
                a = divisor * quotient
                b = divisor
            else:
                a = _math_rand_int(rng, 2, 12)
                b = _math_rand_int(rng, 2, 12)

        items.append(
            {
                'n': i + 1,
                'a': a,
                'b': b,
                'op': op,
                'text': f"{a} {_math_op_symbol(op)} {b} =",
            }
        )

    return items


def _normalize_word(text: str) -> str:
    return (text or '').strip().replace(' ', '').upper()


def _generate_word_letter_bank(rng: random.Random, word: str) -> list:
    base = list(word)
    extra_count = min(2, max(0, 8 - len(base)))
    extra = []
    while len(extra) < extra_count:
        ch = UKR_ALPHABET[_math_rand_int(rng, 0, len(UKR_ALPHABET) - 1)]
        if ch not in base and ch not in extra:
            extra.append(ch)
    letters = base + extra
    rng.shuffle(letters)
    return letters


def _generate_words_items_for_user(rng: random.Random, user, total: int = 10):
    if getattr(user, 'is_authenticated', False):
        qs = (
            WordPuzzleWord.objects.filter(is_active=True, created_by=user)
            .only('word', 'hint', 'emoji')
            .order_by('-created_at')
        )
    else:
        qs = []
    pool = [
        {
            'word': _normalize_word(w.word),
            'hint': (w.hint or '').strip(),
            'emoji': (w.emoji or '').strip() or '🧩',
        }
        for w in qs
        if _normalize_word(w.word)
    ]
    if not pool:
        pool = [
            { 'word': 'КІТ', 'hint': 'Домашній улюбленець, який муркоче', 'emoji': '🐱' },
            { 'word': 'ЛІС', 'hint': 'Багато дерев, можна почути пташок', 'emoji': '🌲' },
            { 'word': 'ДОЩ', 'hint': 'Капає з неба, потрібна парасоля', 'emoji': '🌧️' },
            { 'word': 'СОНЦЕ', 'hint': 'Світить вдень і гріє', 'emoji': '☀️' },
            { 'word': 'РИБА', 'hint': 'Плаває у воді', 'emoji': '🐟' },
            { 'word': 'КВІТКА', 'hint': 'Росте на клумбі і пахне', 'emoji': '🌸' },
            { 'word': 'МОРЕ', 'hint': 'Солона вода і хвилі', 'emoji': '🌊' },
            { 'word': 'ПТАХ', 'hint': 'Має крила і літає', 'emoji': '🐦' },
            { 'word': 'ВІТЕР', 'hint': 'Невидимий, але рухає листя', 'emoji': '💨' },
            { 'word': 'СНІГ', 'hint': 'Білий, падає взимку', 'emoji': '❄️' },
        ]

    # Prefer unique items if possible.
    rng.shuffle(pool)
    picked = pool[:total]
    while len(picked) < total:
        picked.append(rng.choice(pool))

    items = []
    for idx, it in enumerate(picked, start=1):
        word = it['word']
        items.append(
            {
                'n': idx,
                'emoji': it.get('emoji') or '🧩',
                'hint': it.get('hint') or '',
                'word_len': len(word),
                'blanks': [''] * len(word),
                'letters': _generate_word_letter_bank(rng, word),
            }
        )
    return items


def _tokenize_sentence(sentence: str) -> list:
    return [t.strip() for t in (sentence or '').split() if t.strip()]


def _generate_sentences_items_for_user(rng: random.Random, user, total: int = 10):
    if getattr(user, 'is_authenticated', False):
        qs = (
            SentenceExercise.objects.filter(is_active=True, created_by=user)
            .only('prompt', 'sentence', 'emoji')
            .order_by('-created_at')
        )
    else:
        qs = []
    pool = [
        {
            'prompt': (ex.prompt or '').strip(),
            'sentence': (ex.sentence or '').strip(),
            'emoji': (ex.emoji or '').strip() or '🧩',
        }
        for ex in qs
        if (ex.prompt or '').strip() and (ex.sentence or '').strip()
    ]
    if not pool:
        pool = [
            { 'prompt': 'Склади речення про котика', 'sentence': 'Кіт спить на дивані.', 'emoji': '🐱' },
            { 'prompt': 'Склади речення про сонце', 'sentence': 'Сонце світить у небі.', 'emoji': '☀️' },
            { 'prompt': 'Склади речення про дощ', 'sentence': 'Дощ капає з хмар.', 'emoji': '🌧️' },
            { 'prompt': 'Склади речення про маму', 'sentence': 'Мама читає мені казку.', 'emoji': '📖' },
            { 'prompt': 'Склади речення про ліс', 'sentence': 'У лісі співають пташки.', 'emoji': '🌲' },
        ]

    rng.shuffle(pool)
    picked = pool[:total]
    while len(picked) < total:
        picked.append(rng.choice(pool))

    items = []
    for idx, it in enumerate(picked, start=1):
        tokens = _tokenize_sentence(it['sentence'])
        bank = _shuffle_with_rng(rng, tokens)
        items.append(
            {
                'n': idx,
                'emoji': it.get('emoji') or '🧩',
                'prompt': it.get('prompt') or '',
                'tokens': bank,
            }
        )
    return items


def _svg_for_attention_task(shapes: list) -> str:
    parts = [
        '<svg class="att-svg" viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Зображення">',
        '<rect x="0" y="0" width="200" height="120" rx="10" fill="#f7f7fb" stroke="#d6d6e7"/>'
    ]
    for s in shapes:
        t = s['type']
        x = s['x']
        y = s['y']
        color = s['color']
        if t == 'circle':
            parts.append(f'<circle cx="{x}" cy="{y}" r="12" fill="{color}" />')
        elif t == 'rect':
            parts.append(f'<rect x="{x-12}" y="{y-12}" width="24" height="24" rx="5" fill="{color}" />')
        else:
            # triangle
            parts.append(f'<path d="M {x} {y-14} L {x-14} {y+12} L {x+14} {y+12} Z" fill="{color}" />')
    parts.append('</svg>')
    return ''.join(parts)


def _attention_grid_positions(rng: random.Random, count: int):
    count = max(1, int(count))

    # Keep shapes reasonably spaced inside 200x120 viewBox.
    if count <= 8:
        cols = 4
    elif count <= 15:
        cols = 5
    else:
        cols = 6

    rows = (count + cols - 1) // cols
    rows = max(2, rows)

    x_min, x_max = 34, 166
    y_min, y_max = 26, 94

    def linspace(a: int, b: int, n: int):
        if n <= 1:
            return [int((a + b) / 2)]
        step = (b - a) / (n - 1)
        return [int(round(a + step * i)) for i in range(n)]

    xs = linspace(x_min, x_max, cols)
    ys = linspace(y_min, y_max, rows)

    cells = []
    for y in ys:
        for x in xs:
            # Tiny jitter to avoid perfect grid.
            jx = rng.randint(-4, 4)
            jy = rng.randint(-4, 4)
            cells.append((x + jx, y + jy))

    rng.shuffle(cells)
    return cells[:count]


def _generate_attention_items(
    rng: random.Random,
    total: int = 10,
    *,
    shapes_count: int = 8,
    diffs_count: int = 5,
):
    palette = ['#ff6b6b', '#ffd166', '#06d6a0', '#118ab2', '#9b5de5', '#f15bb5']
    types = ['circle', 'rect', 'tri']

    shapes_count = max(5, int(shapes_count))
    diffs_count = max(1, min(int(diffs_count), 5))
    diffs_count = min(diffs_count, shapes_count)

    items = []
    for idx in range(total):
        positions = _attention_grid_positions(rng, shapes_count)
        base = []
        for (x, y) in positions:
            base.append(
                {
                    'type': rng.choice(types),
                    'x': x,
                    'y': y,
                    'color': rng.choice(palette),
                }
            )

        right = [dict(s) for s in base]
        diff_idx = _shuffle_with_rng(rng, list(range(len(right))))[:diffs_count]
        for j in diff_idx:
            old = right[j]
            # Change color to a different palette color.
            new_color = rng.choice([c for c in palette if c != old['color']])
            right[j] = {**old, 'color': new_color}

        diff_set = set(diff_idx)
        targets = []
        for j, s in enumerate(right):
            targets.append(
                {
                    'id': f's{j}',
                    # viewBox is 200x120 in _svg_for_attention_task
                    'x': s['x'],
                    'y': s['y'],
                    # click radius in viewBox units
                    'r': 18,
                    'is_diff': j in diff_set,
                }
            )

        diffs = [t for t in targets if t.get('is_diff')]

        items.append(
            {
                'n': idx + 1,
                'left_svg': _svg_for_attention_task(base),
                'right_svg': _svg_for_attention_task(right),
                'diffs': diffs,
                'targets': targets,
            }
        )
    return items


def _generate_memory_items(rng: random.Random, total: int = 10):
    # Printable Memory (educational): match emoji to the correct word.
    # Left column: emoji, Right column: shuffled words.
    bank = [
        {'id': 'sun', 'label': 'Сонце', 'ico': '☀️'},
        {'id': 'moon', 'label': 'Місяць', 'ico': '🌙'},
        {'id': 'star', 'label': 'Зірка', 'ico': '⭐'},
        {'id': 'heart', 'label': 'Серце', 'ico': '❤️'},
        {'id': 'leaf', 'label': 'Листок', 'ico': '🍃'},
        {'id': 'music', 'label': 'Нота', 'ico': '🎵'},
        {'id': 'cat', 'label': 'Кіт', 'ico': '🐱'},
        {'id': 'dog', 'label': 'Пес', 'ico': '🐶'},
        {'id': 'fish', 'label': 'Рибка', 'ico': '🐟'},
        {'id': 'car', 'label': 'Машина', 'ico': '🚗'},
        {'id': 'apple', 'label': 'Яблуко', 'ico': '🍎'},
        {'id': 'pear', 'label': 'Груша', 'ico': '🍐'},
        {'id': 'banana', 'label': 'Банан', 'ico': '🍌'},
        {'id': 'book', 'label': 'Книга', 'ico': '📖'},
        {'id': 'ball', 'label': 'М’яч', 'ico': '⚽'},
        {'id': 'flower', 'label': 'Квітка', 'ico': '🌸'},
        {'id': 'tree', 'label': 'Дерево', 'ico': '🌳'},
        {'id': 'snow', 'label': 'Сніг', 'ico': '❄️'},
        {'id': 'rain', 'label': 'Дощ', 'ico': '🌧️'},
        {'id': 'cake', 'label': 'Торт', 'ico': '🎂'},
    ]

    total = max(4, min(int(total), 10))
    if len(bank) >= total:
        chosen = rng.sample(bank, k=total)
    else:
        chosen = [rng.choice(bank) for _ in range(total)]

    left_tags = [str(i) for i in range(1, total + 1)]
    right_tags = list('ABCDEFGHIJ')[:total]

    left = []
    for idx, it in enumerate(chosen):
        left.append({'tag': left_tags[idx], 'ico': it['ico'], 'label': it['label'], 'id': it['id']})

    right = [dict(x) for x in left]
    rng.shuffle(right)
    for idx, it in enumerate(right):
        it['tag'] = right_tags[idx]

    return [{'n': 1, 'left': left, 'right': right}]


@login_required
def specialist_print(request):
    if not _require_specialist(request):
        return redirect('child_profile')

    context = {
        'layout': 'specialist',
        'hub_url_name': 'specialist_print',
        'math_url_name': 'specialist_print_math',
        'sentences_url_name': 'specialist_print_sentences',
        'words_url_name': 'specialist_print_words',
        'attention_url_name': 'specialist_print_attention',
        'memory_url_name': 'specialist_print_memory',
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
    }
    return render(request, 'print/hub.html', context)


@login_required
def specialist_print_math(request):
    if not _require_specialist(request):
        return redirect('child_profile')

    rng = random.Random()
    level = _parse_choice(request, 'level', {'easy', 'medium', 'hard'}, 'easy')
    op = _parse_choice(request, 'op', {'mix', 'add', 'sub', 'mul', 'div'}, 'mix')

    items = _generate_math_items(rng, level=level, op_mode=op, total=10)

    context = {
        'layout': 'specialist',
        'hub_url_name': 'specialist_print',
        'self_url_name': 'specialist_print_math',
        'title': 'Математика',
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'level': level,
        'op': op,
        'items': items,
    }
    return render(request, 'print/math.html', context)


@login_required
def specialist_print_sentences(request):
    if not _require_specialist(request):
        return redirect('child_profile')

    rng = random.Random()
    items = _generate_sentences_items_for_user(rng, request.user, total=10)

    context = {
        'layout': 'specialist',
        'hub_url_name': 'specialist_print',
        'self_url_name': 'specialist_print_sentences',
        'title': 'Побудова речень',
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'items': items,
    }
    return render(request, 'print/sentences.html', context)


@login_required
def specialist_print_words(request):
    if not _require_specialist(request):
        return redirect('child_profile')

    rng = random.Random()
    items = _generate_words_items_for_user(rng, request.user, total=10)

    context = {
        'layout': 'specialist',
        'hub_url_name': 'specialist_print',
        'self_url_name': 'specialist_print_words',
        'title': 'Пазли слів',
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'items': items,
    }
    return render(request, 'print/words.html', context)


@login_required
def specialist_print_attention(request):
    if not _require_specialist(request):
        return redirect('child_profile')

    rng = random.Random()
    items = _generate_attention_items(rng, total=10)

    context = {
        'layout': 'specialist',
        'hub_url_name': 'specialist_print',
        'self_url_name': 'specialist_print_attention',
        'title': 'Увага',
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'items': items,
    }
    return render(request, 'print/attention.html', context)


@login_required
def specialist_print_memory(request):
    if not _require_specialist(request):
        return redirect('child_profile')

    rng = random.Random()
    items = _generate_memory_items(rng, total=10)

    context = {
        'layout': 'specialist',
        'hub_url_name': 'specialist_print',
        'self_url_name': 'specialist_print_memory',
        'title': "Памʼять",
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'items': items,
    }
    return render(request, 'print/memory.html', context)


def print_hub(request):
    stars = getattr(getattr(request.user, 'child_profile', None), 'stars', None) if request.user.is_authenticated else None
    context = {
        'layout': 'public',
        'hub_url_name': 'print_hub',
        'math_url_name': 'print_math',
        'sentences_url_name': 'print_sentences',
        'words_url_name': 'print_words',
        'attention_url_name': 'print_attention',
        'memory_url_name': 'print_memory',
        'stars': stars,
        'username': request.user.username if request.user.is_authenticated else 'Гість',
    }
    return render(request, 'print/hub.html', context)


def print_math(request):
    stars = getattr(getattr(request.user, 'child_profile', None), 'stars', None) if request.user.is_authenticated else None

    rng = random.Random()
    level = _parse_choice(request, 'level', {'easy', 'medium', 'hard'}, 'easy')
    op = _parse_choice(request, 'op', {'mix', 'add', 'sub', 'mul', 'div'}, 'mix')
    items = _generate_math_items(rng, level=level, op_mode=op, total=10)

    context = {
        'layout': 'public',
        'hub_url_name': 'print_hub',
        'self_url_name': 'print_math',
        'stars': stars,
        'title': 'Математика',
        'username': request.user.username if request.user.is_authenticated else 'Гість',
        'level': level,
        'op': op,
        'items': items,
    }
    return render(request, 'print/math.html', context)


def print_sentences(request):
    stars = getattr(getattr(request.user, 'child_profile', None), 'stars', None) if request.user.is_authenticated else None

    rng = random.Random()
    items = _generate_sentences_items_for_user(rng, request.user, total=10)

    context = {
        'layout': 'public',
        'hub_url_name': 'print_hub',
        'self_url_name': 'print_sentences',
        'stars': stars,
        'title': 'Побудова речень',
        'username': request.user.username if request.user.is_authenticated else 'Гість',
        'items': items,
    }
    return render(request, 'print/sentences.html', context)


def print_words(request):
    stars = getattr(getattr(request.user, 'child_profile', None), 'stars', None) if request.user.is_authenticated else None

    rng = random.Random()
    items = _generate_words_items_for_user(rng, request.user, total=10)

    context = {
        'layout': 'public',
        'hub_url_name': 'print_hub',
        'self_url_name': 'print_words',
        'stars': stars,
        'title': 'Пазли слів',
        'username': request.user.username if request.user.is_authenticated else 'Гість',
        'items': items,
    }
    return render(request, 'print/words.html', context)


def print_attention(request):
    stars = getattr(getattr(request.user, 'child_profile', None), 'stars', None) if request.user.is_authenticated else None

    rng = random.Random()
    items = _generate_attention_items(rng, total=10)

    context = {
        'layout': 'public',
        'hub_url_name': 'print_hub',
        'self_url_name': 'print_attention',
        'stars': stars,
        'title': 'Увага',
        'username': request.user.username if request.user.is_authenticated else 'Гість',
        'items': items,
    }
    return render(request, 'print/attention.html', context)


def print_memory(request):
    stars = getattr(getattr(request.user, 'child_profile', None), 'stars', None) if request.user.is_authenticated else None

    rng = random.Random()
    items = _generate_memory_items(rng, total=10)

    context = {
        'layout': 'public',
        'hub_url_name': 'print_hub',
        'self_url_name': 'print_memory',
        'stars': stars,
        'title': "Памʼять",
        'username': request.user.username if request.user.is_authenticated else 'Гість',
        'items': items,
    }
    return render(request, 'print/memory.html', context)


@login_required
@require_POST
def specialist_add_student(request):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    specialist = request.user.specialist_profile
    child_id = request.POST.get('child_id')
    try:
        child_id_int = int(child_id)
    except (TypeError, ValueError):
        return redirect('specialist_profile')

    target = ChildProfile.objects.filter(id=child_id_int).first()
    if target:
        specialist.students.add(target)

    next_url = request.POST.get('next') or reverse('specialist_profile')
    return redirect(next_url)


@login_required
@require_POST
def specialist_remove_student(request, child_profile_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    specialist = request.user.specialist_profile
    specialist.students.remove(child_profile_id)
    next_url = request.POST.get('next') or reverse('specialist_profile')
    return redirect(next_url)


@login_required
def specialist_student_stats(request, child_profile_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    specialist = request.user.specialist_profile
    child = specialist.students.select_related('user').filter(id=child_profile_id).first()
    if not child:
        return redirect('specialist_profile')

    # "Рекомендації" прибрано: статистика доступна у "Нотатки".
    return redirect('specialist_student_notes', child_profile_id=child.id)


@login_required
def specialist_student_notes(request, child_profile_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    specialist = request.user.specialist_profile
    child = specialist.students.select_related('user').filter(id=child_profile_id).first()
    if not child:
        return redirect('specialist_profile')

    if request.method == 'POST':
        form = SpecialistStudentNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.specialist = specialist
            note.student = child
            note.save()
            return redirect('specialist_student_notes', child_profile_id=child.id)
    else:
        form = SpecialistStudentNoteForm()

    notes = list(
        SpecialistStudentNote.objects.filter(specialist=specialist, student=child)
        .only('id', 'text', 'created_at')
        .order_by('-created_at')
    )

    stats = _build_child_stats_for_user(child.user)
    avg = stats.get('avg') or {}
    focus_candidates = [
        ('Математика', int(avg.get('math') or 0)),
        ("Памʼять", int(avg.get('memory') or 0)),
        ('Звуки', int(avg.get('sound') or 0)),
        ('Пазли слів', int(avg.get('words') or 0)),
        ('Побудова речень', int(avg.get('sentences') or 0)),
    ]
    focus_label, focus_value = min(focus_candidates, key=lambda x: x[1])
    focus_severity = max(0, min(100, 100 - int(focus_value)))

    context = {
        'username': request.user.username,
        'student': child,
        'form': form,
        'notes': notes,
        'stats': stats,
        'focus_label': focus_label,
        'focus_value': int(focus_value),
        'focus_severity': int(focus_severity),
        'results_count': stats['results_count'],
        'stories_listens_count': stats['stories_listens_count'],
        'progress': stats['progress'],
        'line_labels': stats['line_labels'],
        'line_datasets': stats['line_datasets'],
        'radar_labels': stats['radar_labels'],
        'radar_values': stats['radar_values'],
    }
    return render(request, 'profile/specialist_notes.html', context)


@login_required
@require_POST
def specialist_student_note_delete(request, note_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    specialist = request.user.specialist_profile
    note = SpecialistStudentNote.objects.filter(id=note_id, specialist=specialist).only('id', 'student_id').first()
    if not note:
        return redirect('specialist_profile')

    child_id = note.student_id
    note.delete()
    return redirect('specialist_student_notes', child_profile_id=child_id)


@login_required
def specialist_coloring_pages(request):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    if request.method == 'POST':
        form = ColoringPageForm(request.POST, request.FILES)
        if form.is_valid():
            page = form.save(commit=False)
            page.created_by = request.user
            page.save()
            return redirect('specialist_coloring_pages')
    else:
        form = ColoringPageForm(initial={'is_active': True})

    pages = list(
        ColoringPage.objects.filter(created_by=request.user)
        .only('id', 'title', 'file', 'file_type', 'is_active', 'created_at')
        .order_by('-created_at')
    )

    safe_pages = []
    for p in pages:
        url = ''
        try:
            if p.file and p.file.storage.exists(p.file.name):
                url = p.file.url
        except Exception:
            url = ''
        safe_pages.append(
            {
                'id': p.id,
                'title': p.title,
                'file_url': url,
                'file_type': p.file_type,
                'is_active': p.is_active,
                'created_at': p.created_at,
            }
        )

    context = {
        'username': request.user.username,
        'form': form,
        'pages': safe_pages,
    }
    return render(request, 'profile/specialist_coloring_pages.html', context)


@login_required
@require_POST
def specialist_coloring_page_delete(request, page_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    ColoringPage.objects.filter(id=page_id, created_by=request.user).delete()
    next_url = request.POST.get('next') or reverse('specialist_coloring_pages')
    return redirect(next_url)


@login_required
def specialist_sounds(request):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    if request.method == 'POST':
        form = SoundCardForm(request.POST, request.FILES)
        if form.is_valid():
            card = form.save(commit=False)
            card.created_by = request.user
            card.save()
            return redirect('specialist_sounds')
    else:
        form = SoundCardForm()

    cards = list(
        SoundCard.objects.filter(created_by=request.user)
        .only('id', 'title', 'image', 'audio', 'created_at')
        .order_by('-created_at')
    )

    for c in cards:
        image_url = ''
        audio_url = ''

        if c.image:
            try:
                if c.image.storage.exists(c.image.name):
                    image_url = c.image.url
            except Exception:
                image_url = ''

        if c.audio:
            try:
                if c.audio.storage.exists(c.audio.name):
                    audio_url = c.audio.url
            except Exception:
                audio_url = ''

        c.safe_image_url = image_url
        c.safe_audio_url = audio_url

    context = {
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'form': form,
        'cards': cards,
    }
    return render(request, 'profile/specialist_sounds.html', context)


@login_required
def specialist_sound_edit(request, card_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    card = SoundCard.objects.filter(id=card_id, created_by=request.user).first()
    if not card:
        return redirect('specialist_sounds')

    if request.method != 'POST':
        return redirect('specialist_sounds')

    if request.method == 'POST':
        old_image = card.image
        old_audio = card.audio
        form = SoundCardForm(request.POST, request.FILES, instance=card)
        if form.is_valid():
            updated = form.save(commit=False)
            # If user uploaded new files, delete old ones.
            if 'image' in request.FILES and old_image:
                try:
                    old_image.delete(save=False)
                except Exception:
                    pass
            if 'audio' in request.FILES and old_audio:
                try:
                    old_audio.delete(save=False)
                except Exception:
                    pass
            updated.save()
            return redirect('specialist_sounds')

        cards = list(
            SoundCard.objects.filter(created_by=request.user)
            .only('id', 'title', 'image', 'audio', 'created_at')
            .order_by('-created_at')
        )

    context = {
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'form': form,
        'cards': cards,
        'edit_card_id': card.id,
    }
    return render(request, 'profile/specialist_sounds.html', context)


@login_required
@require_POST
def specialist_sound_delete(request, card_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    card = SoundCard.objects.filter(id=card_id, created_by=request.user).first()
    if card:
        # Best-effort cleanup of stored files.
        try:
            if card.image:
                card.image.delete(save=False)
        except Exception:
            pass
        try:
            if card.audio:
                card.audio.delete(save=False)
        except Exception:
            pass
        card.delete()

    next_url = request.POST.get('next') or reverse('specialist_sounds')
    return redirect(next_url)


@login_required
def specialist_stories(request):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.created_by = request.user
            story.save()
            return redirect('specialist_stories')
    else:
        form = StoryForm()

    stories = list(
        Story.objects.filter(created_by=request.user)
        .only('id', 'title', 'content_type', 'image', 'text', 'pdf_file', 'audio', 'created_at')
        .order_by('-created_at')
    )

    for s in stories:
        image_url = ''
        pdf_url = ''
        audio_url = ''

        if s.image:
            try:
                if s.image.storage.exists(s.image.name):
                    image_url = s.image.url
            except Exception:
                image_url = ''

        if s.pdf_file:
            try:
                if s.pdf_file.storage.exists(s.pdf_file.name):
                    pdf_url = s.pdf_file.url
            except Exception:
                pdf_url = ''

        if s.audio:
            try:
                if s.audio.storage.exists(s.audio.name):
                    audio_url = s.audio.url
            except Exception:
                audio_url = ''

        s.safe_pdf_url = pdf_url
        s.safe_audio_url = audio_url
        s.safe_image_url = image_url

    context = {
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'form': form,
        'stories': stories,
    }
    return render(request, 'profile/specialist_stories.html', context)


@login_required
def specialist_story_edit(request, story_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    story = Story.objects.filter(id=story_id, created_by=request.user).first()
    if not story:
        return redirect('specialist_stories')

    if request.method != 'POST':
        return redirect('specialist_stories')

    old_pdf = story.pdf_file
    old_audio = story.audio
    old_image = story.image

    form = StoryForm(request.POST, request.FILES, instance=story)
    if form.is_valid():
        updated = form.save(commit=False)
        # If switching to TEXT, delete old PDF.
        if updated.content_type == Story.ContentType.TEXT and old_pdf:
            try:
                old_pdf.delete(save=False)
            except Exception:
                pass
            updated.pdf_file = None

        # If uploading new PDF, delete old.
        if 'pdf_file' in request.FILES and old_pdf:
            try:
                old_pdf.delete(save=False)
            except Exception:
                pass

        # If uploading new image, delete old.
        if 'image' in request.FILES and old_image:
            try:
                old_image.delete(save=False)
            except Exception:
                pass

        # If uploading new audio, delete old.
        if 'audio' in request.FILES and old_audio:
            try:
                old_audio.delete(save=False)
            except Exception:
                pass

        updated.save()
        return redirect('specialist_stories')

    stories = list(
        Story.objects.filter(created_by=request.user)
        .only('id', 'title', 'content_type', 'image', 'text', 'pdf_file', 'audio', 'created_at')
        .order_by('-created_at')
    )
    for s in stories:
        image_url = ''
        pdf_url = ''
        audio_url = ''
        if s.image:
            try:
                if s.image.storage.exists(s.image.name):
                    image_url = s.image.url
            except Exception:
                image_url = ''
        if s.pdf_file:
            try:
                if s.pdf_file.storage.exists(s.pdf_file.name):
                    pdf_url = s.pdf_file.url
            except Exception:
                pdf_url = ''
        if s.audio:
            try:
                if s.audio.storage.exists(s.audio.name):
                    audio_url = s.audio.url
            except Exception:
                audio_url = ''
        s.safe_pdf_url = pdf_url
        s.safe_audio_url = audio_url
        s.safe_image_url = image_url

    context = {
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'form': form,
        'stories': stories,
        'edit_story_id': story.id,
    }
    return render(request, 'profile/specialist_stories.html', context)


@login_required
@require_POST
def specialist_story_delete(request, story_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    story = Story.objects.filter(id=story_id, created_by=request.user).first()
    if story:
        try:
            if story.pdf_file:
                story.pdf_file.delete(save=False)
        except Exception:
            pass
        try:
            if story.audio:
                story.audio.delete(save=False)
        except Exception:
            pass
        try:
            if story.image:
                story.image.delete(save=False)
        except Exception:
            pass
        story.delete()

    next_url = request.POST.get('next') or reverse('specialist_stories')
    return redirect(next_url)
@login_required
def specialist_words(request):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    if request.method == 'POST':
        form = WordPuzzleWordForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()
            return redirect('specialist_words')
    else:
        form = WordPuzzleWordForm(initial={'is_active': True})

    words = list(
        WordPuzzleWord.objects.filter(created_by=request.user)
        .only('id', 'word', 'hint', 'emoji', 'is_active', 'created_at')
        .order_by('-created_at')
    )

    context = {
        'username': request.user.username,
        'coins': request.user.specialist_profile.coins,
        'form': form,
        'words': words,
    }
    return render(request, 'profile/specialist_words.html', context)


@login_required
@require_POST
def specialist_word_delete(request, word_id: int):
    if not hasattr(request.user, 'specialist_profile'):
        return redirect('child_profile')

    WordPuzzleWord.objects.filter(id=word_id, created_by=request.user).delete()
    next_url = request.POST.get('next') or reverse('specialist_words')
    return redirect(next_url)


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
    if game_type not in (
        GameResult.GameType.MATH,
        GameResult.GameType.MEMORY,
        GameResult.GameType.SOUND,
        GameResult.GameType.WORDS,
        GameResult.GameType.SENTENCES,
    ):
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

    profile, _created = ChildProfile.objects.get_or_create(user=request.user, defaults={'stars': 0})
    stars_earned = max(1, int(score // 20))
    ChildProfile.objects.filter(id=profile.id).update(stars=F('stars') + stars_earned)

    # Badge rules
    total_results = GameResult.objects.filter(user=request.user).count()
    if total_results == 1:
        _award_badge(request.user, 'first_game')

    counts_by_game = {
        GameResult.GameType.MATH: GameResult.objects.filter(user=request.user, game_type=GameResult.GameType.MATH).count(),
        GameResult.GameType.MEMORY: GameResult.objects.filter(user=request.user, game_type=GameResult.GameType.MEMORY).count(),
        GameResult.GameType.SOUND: GameResult.objects.filter(user=request.user, game_type=GameResult.GameType.SOUND).count(),
        GameResult.GameType.WORDS: GameResult.objects.filter(user=request.user, game_type=GameResult.GameType.WORDS).count(),
    }
    if counts_by_game[GameResult.GameType.MATH] >= 5:
        _award_badge(request.user, 'math_5')
    if counts_by_game[GameResult.GameType.MEMORY] >= 5:
        _award_badge(request.user, 'memory_5')
    if counts_by_game[GameResult.GameType.WORDS] >= 5:
        _award_badge(request.user, 'words_5')
    if counts_by_game[GameResult.GameType.SOUND] >= 5:
        _award_badge(request.user, 'sound_5')

    new_total = ChildProfile.objects.filter(id=profile.id).values_list('stars', flat=True).first() or 0
    return JsonResponse({'ok': True, 'id': result.id, 'stars_earned': stars_earned, 'stars_total': new_total})


@login_required
@require_POST
def record_story_listen(request):
    if hasattr(request.user, 'specialist_profile'):
        return JsonResponse({'ok': False, 'error': 'specialist_cannot_record'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)

    story_id = payload.get('story_id')
    try:
        story_id = int(story_id)
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'invalid_story_id'}, status=400)

    story = Story.objects.filter(id=story_id, is_active=True).only('id').first()
    if not story:
        return JsonResponse({'ok': False, 'error': 'story_not_found'}, status=404)

    # Award stars for a first-time listen of this story.
    first_time_for_story = not StoryListen.objects.filter(user=request.user, story_id=story_id).exists()

    duration_seconds = payload.get('duration_seconds')
    if duration_seconds is not None:
        try:
            duration_seconds = int(duration_seconds)
        except (TypeError, ValueError):
            duration_seconds = None
        if duration_seconds is not None and duration_seconds < 0:
            duration_seconds = None

    listen = StoryListen.objects.create(user=request.user, story=story, duration_seconds=duration_seconds)

    profile, _created = ChildProfile.objects.get_or_create(user=request.user, defaults={'stars': 0})
    stars_earned = 0
    if first_time_for_story:
        stars_earned = 2
        ChildProfile.objects.filter(id=profile.id).update(stars=F('stars') + stars_earned)

    listened_unique = (
        StoryListen.objects.filter(user=request.user)
        .values('story_id')
        .distinct()
        .count()
    )
    if listened_unique >= 3:
        _award_badge(request.user, 'stories_3')

    new_total = ChildProfile.objects.filter(id=profile.id).values_list('stars', flat=True).first() or 0
    return JsonResponse({'ok': True, 'id': listen.id, 'stars_earned': stars_earned, 'stars_total': new_total})
