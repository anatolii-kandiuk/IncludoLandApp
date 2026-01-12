from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


def home(request):
    context = {
        'stars': 1250,
    }
    return render(request, 'home.html', context)


def games(request):
    context = {
        'stars': 1250,
    }
    return render(request, 'games.html', context)


@ensure_csrf_cookie
def game_memory(request):
    context = {
        'stars': 1250,
    }
    return render(request, 'games/memory.html', context)


@ensure_csrf_cookie
def game_math(request):
    context = {
        'stars': 1250,
    }
    return render(request, 'games/math.html', context)


def coming_soon(request, section: str):
    return render(request, 'coming_soon.html', {'section': section})
