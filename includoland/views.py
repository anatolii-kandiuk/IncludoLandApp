import json

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from accounts.models import SentenceExercise, SoundCard, Story, WordPuzzleWord


def _child_stars(request):
    profile = getattr(request.user, 'child_profile', None)
    return getattr(profile, 'stars', None)


def home(request):
    context = {
        'stars': _child_stars(request),
    }
    return render(request, 'home.html', context)


def games(request):
    # Games are shown on the home page now.
    return redirect(f"{reverse('home')}#games")


@ensure_csrf_cookie
def game_memory(request):
    context = {
        'stars': _child_stars(request),
    }
    return render(request, 'games/memory.html', context)


@ensure_csrf_cookie
def game_math(request):
    context = {
        'stars': _child_stars(request),
    }
    return render(request, 'games/math.html', context)


@ensure_csrf_cookie
def game_sounds(request):
    candidates = (
        SoundCard.objects.filter(is_active=True)
        .only('id', 'title', 'image', 'audio')
        .order_by('-created_at')
    )

    sound_cards_payload = []
    for c in candidates:
        if not c.image or not c.audio:
            continue
        try:
            if not c.image.storage.exists(c.image.name):
                continue
            if not c.audio.storage.exists(c.audio.name):
                continue
        except Exception:
            # If storage is unavailable/misconfigured, don't break the game page.
            continue

        sound_cards_payload.append(
            {
                'id': c.id,
                'label': c.title,
                'image_url': c.image.url,
                'audio_url': c.audio.url,
            }
        )
    context = {
        'stars': _child_stars(request),
        'sound_cards_json': json.dumps(sound_cards_payload, ensure_ascii=False),
    }
    return render(request, 'games/sounds.html', context)


@ensure_csrf_cookie
def game_attention(request):
    context = {
        'stars': _child_stars(request),
    }
    return render(request, 'games/attention.html', context)


@ensure_csrf_cookie
def game_words(request):
    qs = WordPuzzleWord.objects.filter(is_active=True).only('word', 'hint', 'emoji', 'created_by')

    # If specialist opens the game, show their own words.
    if request.user.is_authenticated and hasattr(request.user, 'specialist_profile'):
        qs = qs.filter(created_by=request.user)

    # If child has assigned specialists, show words added by those specialists.
    if request.user.is_authenticated and hasattr(request.user, 'child_profile'):
        specialists = list(request.user.child_profile.specialists.select_related('user'))
        if specialists:
            qs = qs.filter(created_by__in=[s.user for s in specialists])

    payload = []
    for w in qs.order_by('-created_at')[:200]:
        word = (w.word or '').strip()
        if not word:
            continue
        payload.append(
            {
                'word': word,
                'hint': w.hint or '',
                'emoji': w.emoji or '🧩',
            }
        )

    context = {
        'stars': _child_stars(request),
        'words_json': json.dumps(payload, ensure_ascii=False),
    }
    return render(request, 'games/words.html', context)


@ensure_csrf_cookie
def game_sentences(request):
    qs = SentenceExercise.objects.filter(is_active=True).only('id', 'prompt', 'sentence', 'emoji', 'created_by')

    # If specialist opens the game, show their own exercises.
    if request.user.is_authenticated and hasattr(request.user, 'specialist_profile'):
        qs = qs.filter(created_by=request.user)

    # If child has assigned specialists, show exercises added by those specialists.
    if request.user.is_authenticated and hasattr(request.user, 'child_profile'):
        specialists = list(request.user.child_profile.specialists.select_related('user'))
        if specialists:
            qs = qs.filter(created_by__in=[s.user for s in specialists])

    payload = []
    for ex in qs.order_by('-created_at')[:200]:
        prompt = (ex.prompt or '').strip()
        sentence = (ex.sentence or '').strip()
        if not prompt or not sentence:
            continue
        payload.append(
            {
                'id': ex.id,
                'prompt': prompt,
                'sentence': sentence,
                'emoji': ex.emoji or '🧩',
            }
        )

    context = {
        'stars': _child_stars(request),
        'sentences_json': json.dumps(payload, ensure_ascii=False),
    }
    return render(request, 'games/sentences.html', context)


def coming_soon(request, section: str):
    return render(request, 'coming_soon.html', {'section': section})


def learn_alphabet(request):
    letters = [
        {'upper': 'А', 'lower': 'а'},
        {'upper': 'Б', 'lower': 'б'},
        {'upper': 'В', 'lower': 'в'},
        {'upper': 'Г', 'lower': 'г'},
        {'upper': 'Ґ', 'lower': 'ґ'},
        {'upper': 'Д', 'lower': 'д'},
        {'upper': 'Е', 'lower': 'е'},
        {'upper': 'Є', 'lower': 'є'},
        {'upper': 'Ж', 'lower': 'ж'},
        {'upper': 'З', 'lower': 'з'},
        {'upper': 'И', 'lower': 'и'},
        {'upper': 'І', 'lower': 'і'},
        {'upper': 'Ї', 'lower': 'ї'},
        {'upper': 'Й', 'lower': 'й'},
        {'upper': 'К', 'lower': 'к'},
        {'upper': 'Л', 'lower': 'л'},
        {'upper': 'М', 'lower': 'м'},
        {'upper': 'Н', 'lower': 'н'},
        {'upper': 'О', 'lower': 'о'},
        {'upper': 'П', 'lower': 'п'},
        {'upper': 'Р', 'lower': 'р'},
        {'upper': 'С', 'lower': 'с'},
        {'upper': 'Т', 'lower': 'т'},
        {'upper': 'У', 'lower': 'у'},
        {'upper': 'Ф', 'lower': 'ф'},
        {'upper': 'Х', 'lower': 'х'},
        {'upper': 'Ц', 'lower': 'ц'},
        {'upper': 'Ч', 'lower': 'ч'},
        {'upper': 'Ш', 'lower': 'ш'},
        {'upper': 'Щ', 'lower': 'щ'},
        {'upper': 'Ь', 'lower': 'ь'},
        {'upper': 'Ю', 'lower': 'ю'},
        {'upper': 'Я', 'lower': 'я'},
    ]

    context = {
        'stars': _child_stars(request),
        'letters': letters,
        'letters_json': json.dumps(letters, ensure_ascii=False),
    }
    return render(request, 'learn/alphabet.html', context)


def learn_alphabet_print(request):
    letters = [
        {'upper': 'А', 'lower': 'а'},
        {'upper': 'Б', 'lower': 'б'},
        {'upper': 'В', 'lower': 'в'},
        {'upper': 'Г', 'lower': 'г'},
        {'upper': 'Ґ', 'lower': 'ґ'},
        {'upper': 'Д', 'lower': 'д'},
        {'upper': 'Е', 'lower': 'е'},
        {'upper': 'Є', 'lower': 'є'},
        {'upper': 'Ж', 'lower': 'ж'},
        {'upper': 'З', 'lower': 'з'},
        {'upper': 'И', 'lower': 'и'},
        {'upper': 'І', 'lower': 'і'},
        {'upper': 'Ї', 'lower': 'ї'},
        {'upper': 'Й', 'lower': 'й'},
        {'upper': 'К', 'lower': 'к'},
        {'upper': 'Л', 'lower': 'л'},
        {'upper': 'М', 'lower': 'м'},
        {'upper': 'Н', 'lower': 'н'},
        {'upper': 'О', 'lower': 'о'},
        {'upper': 'П', 'lower': 'п'},
        {'upper': 'Р', 'lower': 'р'},
        {'upper': 'С', 'lower': 'с'},
        {'upper': 'Т', 'lower': 'т'},
        {'upper': 'У', 'lower': 'у'},
        {'upper': 'Ф', 'lower': 'ф'},
        {'upper': 'Х', 'lower': 'х'},
        {'upper': 'Ц', 'lower': 'ц'},
        {'upper': 'Ч', 'lower': 'ч'},
        {'upper': 'Ш', 'lower': 'ш'},
        {'upper': 'Щ', 'lower': 'щ'},
        {'upper': 'Ь', 'lower': 'ь'},
        {'upper': 'Ю', 'lower': 'ю'},
        {'upper': 'Я', 'lower': 'я'},
    ]

    context = {
        'stars': _child_stars(request),
        'letters': letters,
    }
    return render(request, 'learn/print_alphabet.html', context)


def learn_numbers(request):
    numbers = [{'n': n} for n in range(0, 11)]
    context = {
        'stars': _child_stars(request),
        'numbers': numbers,
        'numbers_json': json.dumps(numbers, ensure_ascii=False),
    }
    return render(request, 'learn/numbers.html', context)


def learn_numbers_print(request):
    numbers = [{'n': n} for n in range(0, 11)]
    context = {
        'stars': _child_stars(request),
        'numbers': numbers,
    }
    return render(request, 'learn/print_numbers.html', context)


def learn_colors(request):
    colors = [
        {'name': 'Червоний', 'hex': '#ef4444'},
        {'name': 'Помаранчевий', 'hex': '#f97316'},
        {'name': 'Жовтий', 'hex': '#f59e0b'},
        {'name': 'Зелений', 'hex': '#22c55e'},
        {'name': 'Блакитний', 'hex': '#38bdf8'},
        {'name': 'Синій', 'hex': '#2563eb'},
        {'name': 'Фіолетовий', 'hex': '#7c3aed'},
        {'name': 'Рожевий', 'hex': '#ec4899'},
        {'name': 'Коричневий', 'hex': '#8b5a2b'},
        {'name': 'Чорний', 'hex': '#111827'},
        {'name': 'Білий', 'hex': '#ffffff'},
    ]
    context = {
        'stars': _child_stars(request),
        'colors': colors,
        'colors_json': json.dumps(colors, ensure_ascii=False),
    }
    return render(request, 'learn/colors.html', context)


def learn_colors_print(request):
    colors = [
        {'name': 'Червоний', 'hex': '#ef4444'},
        {'name': 'Помаранчевий', 'hex': '#f97316'},
        {'name': 'Жовтий', 'hex': '#f59e0b'},
        {'name': 'Зелений', 'hex': '#22c55e'},
        {'name': 'Блакитний', 'hex': '#38bdf8'},
        {'name': 'Синій', 'hex': '#2563eb'},
        {'name': 'Фіолетовий', 'hex': '#7c3aed'},
        {'name': 'Рожевий', 'hex': '#ec4899'},
        {'name': 'Коричневий', 'hex': '#8b5a2b'},
        {'name': 'Чорний', 'hex': '#111827'},
        {'name': 'Білий', 'hex': '#ffffff'},
    ]
    context = {
        'stars': _child_stars(request),
        'colors': colors,
    }
    return render(request, 'learn/print_colors.html', context)


def learn_coloring(request):
    # Simple print-friendly coloring sheets with color hints.
    color_hex = {
        'Червоний': '#ef4444',
        'Помаранчевий': '#f97316',
        'Жовтий': '#f59e0b',
        'Зелений': '#22c55e',
        'Блакитний': '#38bdf8',
        'Синій': '#2563eb',
        'Фіолетовий': '#7c3aed',
        'Рожевий': '#ec4899',
        'Коричневий': '#8b5a2b',
        'Чорний': '#111827',
        'Білий': '#ffffff',
    }

    def _hint(name: str):
        return {'name': name, 'hex': color_hex.get(name, '#e5e7eb')}

    pages = [
        {
            'title': 'Кулька',
            'hints': [_hint('Червоний'), _hint('Синій'), _hint('Жовтий')],
            'svg': (
                '<svg viewBox="0 0 300 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Розмальовка">'
                '<path d="M150 30c-60 0-105 45-105 110 0 86 64 142 105 170 41-28 105-84 105-170 0-65-45-110-105-110z" fill="none" stroke="#111827" stroke-width="6"/>'
                '<path d="M150 310c-16 18-22 32-22 48" fill="none" stroke="#111827" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M150 310c16 18 22 32 22 48" fill="none" stroke="#111827" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M150 340l-18-12" fill="none" stroke="#111827" stroke-width="6" stroke-linecap="round"/>'
                '<path d="M150 340l18-12" fill="none" stroke="#111827" stroke-width="6" stroke-linecap="round"/>'
                '</svg>'
            ),
        },
        {
            'title': 'Будиночок',
            'hints': [_hint('Коричневий'), _hint('Червоний'), _hint('Блакитний'), _hint('Зелений')],
            'svg': (
                '<svg viewBox="0 0 300 380" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Розмальовка">'
                '<path d="M60 170l90-90 90 90" fill="none" stroke="#111827" stroke-width="6" stroke-linejoin="round"/>'
                '<rect x="85" y="170" width="130" height="140" fill="none" stroke="#111827" stroke-width="6"/>'
                '<rect x="135" y="225" width="40" height="85" fill="none" stroke="#111827" stroke-width="6"/>'
                '<rect x="105" y="195" width="38" height="30" fill="none" stroke="#111827" stroke-width="6"/>'
                '<rect x="157" y="195" width="38" height="30" fill="none" stroke="#111827" stroke-width="6"/>'
                '<path d="M20 310h260" fill="none" stroke="#111827" stroke-width="6" stroke-linecap="round"/>'
                '</svg>'
            ),
        },
    ]

    context = {
        'stars': _child_stars(request),
        'pages': pages,
    }
    return render(request, 'learn/coloring.html', context)


def learn_coloring_print(request):
    # Reuse the same generation as learn_coloring.
    color_hex = {
        'Червоний': '#ef4444',
        'Помаранчевий': '#f97316',
        'Жовтий': '#f59e0b',
        'Зелений': '#22c55e',
        'Блакитний': '#38bdf8',
        'Синій': '#2563eb',
        'Фіолетовий': '#7c3aed',
        'Рожевий': '#ec4899',
        'Коричневий': '#8b5a2b',
        'Чорний': '#111827',
        'Білий': '#ffffff',
    }

    def _hint(name: str):
        return {'name': name, 'hex': color_hex.get(name, '#e5e7eb')}

    pages = [
        {
            'title': 'Кулька',
            'hints': [_hint('Червоний'), _hint('Синій'), _hint('Жовтий')],
            'svg': (
                '<svg viewBox="0 0 420 320" xmlns="http://www.w3.org/2000/svg">'
                '<rect x="1" y="1" width="418" height="318" fill="white" stroke="#111827" stroke-width="2"/>'
                '<circle cx="190" cy="140" r="85" fill="none" stroke="#111827" stroke-width="5"/>'
                '<path d="M190 225 C 190 250, 160 260, 160 280" fill="none" stroke="#111827" stroke-width="4"/>'
                '<path d="M190 225 C 190 250, 220 260, 220 280" fill="none" stroke="#111827" stroke-width="4"/>'
                '<path d="M190 225 C 190 255, 190 260, 190 290" fill="none" stroke="#111827" stroke-width="4"/>'
                '</svg>'
            ),
        },
        {
            'title': 'Будинок',
            'hints': [_hint('Коричневий'), _hint('Червоний'), _hint('Блакитний'), _hint('Жовтий')],
            'svg': (
                '<svg viewBox="0 0 420 320" xmlns="http://www.w3.org/2000/svg">'
                '<rect x="1" y="1" width="418" height="318" fill="white" stroke="#111827" stroke-width="2"/>'
                '<rect x="120" y="140" width="180" height="140" fill="none" stroke="#111827" stroke-width="5"/>'
                '<path d="M110 150 L210 70 L310 150" fill="none" stroke="#111827" stroke-width="5"/>'
                '<rect x="190" y="195" width="40" height="85" fill="none" stroke="#111827" stroke-width="5"/>'
                '<rect x="145" y="175" width="45" height="45" fill="none" stroke="#111827" stroke-width="5"/>'
                '<rect x="240" y="175" width="45" height="45" fill="none" stroke="#111827" stroke-width="5"/>'
                '</svg>'
            ),
        },
    ]

    context = {
        'stars': _child_stars(request),
        'pages': pages,
    }
    return render(request, 'learn/print_coloring.html', context)


@ensure_csrf_cookie
def stories_library(request):
    candidates = (
        Story.objects.filter(is_active=True)
        .only('id', 'title', 'content_type', 'image', 'text', 'pdf_file', 'audio', 'created_at')
        .order_by('-created_at')
    )

    stories = []
    for s in candidates:
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

        stories.append(
            {
                'id': s.id,
                'title': s.title,
                'content_type': s.content_type,
                'text': s.text if s.content_type == Story.ContentType.TEXT else '',
                'image_url': image_url,
                'pdf_url': pdf_url,
                'audio_url': audio_url,
            }
        )

    context = {
        'stars': _child_stars(request),
        'stories': stories,
    }
    return render(request, 'stories.html', context)
