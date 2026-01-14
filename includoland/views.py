import json

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from accounts.models import SoundCard, Story


def _child_stars(request):
    profile = getattr(request.user, 'child_profile', None)
    return getattr(profile, 'stars', None)


def home(request):
    context = {
        'stars': _child_stars(request),
    }
    return render(request, 'home.html', context)


def games(request):
    context = {
        'stars': _child_stars(request),
    }
    return render(request, 'games.html', context)


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
    context = {
        'stars': _child_stars(request),
    }
    return render(request, 'games/words.html', context)


def coming_soon(request, section: str):
    return render(request, 'coming_soon.html', {'section': section})


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
