from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


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
    context = {
        'stars': _child_stars(request),
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
