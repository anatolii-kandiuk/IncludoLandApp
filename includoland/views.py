from django.shortcuts import render


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


def coming_soon(request, section: str):
    return render(request, 'coming_soon.html', {'section': section})
