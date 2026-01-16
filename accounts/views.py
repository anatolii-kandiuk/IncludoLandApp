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

from .forms import RegisterForm, SoundCardForm, StoryForm, WordPuzzleWordForm
from .models import ChildProfile, GameResult, SpecialistProfile, SoundCard, Story, StoryListen, UserBadge, WordPuzzleWord


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

    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.MATH).count() >= 5:
        _award_badge(user, 'math_5')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.MEMORY).count() >= 5:
        _award_badge(user, 'memory_5')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.WORDS).count() >= 5:
        _award_badge(user, 'words_5')
    if GameResult.objects.filter(user=user, game_type=GameResult.GameType.SOUND).count() >= 5:
        _award_badge(user, 'sound_5')

    listened_unique = (
        StoryListen.objects.filter(user=user)
        .values('story_id')
        .distinct()
        .count()
    )
    if listened_unique >= 3:
        _award_badge(user, 'stories_3')


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

    def avg_score(game_type: str) -> int:
        values = [r.score for r in results if r.game_type == game_type]
        if not values:
            return 0
        return int(round(sum(values) / len(values)))

    math_avg = avg_score(GameResult.GameType.MATH)
    memory_avg = avg_score(GameResult.GameType.MEMORY)
    sound_avg = avg_score(GameResult.GameType.SOUND)
    words_avg = avg_score(GameResult.GameType.WORDS)

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
        {'label': 'Казки (слухання)', 'value': stories_listen_pct},
    ]

    radar_labels = ['Математика', "Памʼять", 'Звуки', 'Пазли слів', 'Казки']
    radar_values = [math_avg, memory_avg, sound_avg, words_avg, stories_listen_pct]

    line_datasets = [
        {'label': 'Математика', 'data': math_values, 'color': '#2b97e5'},
        {'label': "Памʼять", 'data': memory_values, 'color': '#19b3b9'},
        {'label': 'Звуки', 'data': sound_values, 'color': '#c28b00'},
        {'label': 'Пазли слів', 'data': words_values, 'color': '#7c3aed'},
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

    attention_students = []
    for s in my_students[:6]:
        stats = _build_child_stats_for_user(s.user)
        attention_students.append(
            {
                'id': s.id,
                'name': s.user.username,
                'subtitle': 'Зосередженість: Памʼять',
                'progress': stats['avg']['memory'],
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
        }
        game_labels = {
            GameResult.GameType.MATH: 'Математика',
            GameResult.GameType.MEMORY: "Памʼять",
            GameResult.GameType.SOUND: 'Звуки',
            GameResult.GameType.WORDS: 'Пазли слів',
        }

        if perf_game == 'all':
            for gt in (GameResult.GameType.MATH, GameResult.GameType.MEMORY, GameResult.GameType.SOUND, GameResult.GameType.WORDS):
                perf_datasets.append({'label': game_labels[gt], 'data': build_series(gt), 'color': game_palette[gt]})
        else:
            perf_datasets.append({'label': game_labels.get(perf_game, perf_game), 'data': build_series(perf_game), 'color': game_palette.get(perf_game, '#2b97e5')})

    context = {
        'username': request.user.username,
        'coins': specialist.coins,
        'attention_students': attention_students,
        'my_students': my_students,
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

    stats = _build_child_stats_for_user(child.user)
    context = {
        'student_username': child.user.username,
        'student_stars': child.stars,
        'results_count': stats['results_count'],
        'stories_listens_count': stats['stories_listens_count'],
        'progress': stats['progress'],
        'line_labels': stats['line_labels'],
        'line_datasets': stats['line_datasets'],
        'radar_labels': stats['radar_labels'],
        'radar_values': stats['radar_values'],
    }
    return render(request, 'profile/student_stats.html', context)


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
