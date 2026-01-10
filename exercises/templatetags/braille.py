from django import template

register = template.Library()

# Very small MVP: transliterate basic Ukrainian/Cyrillic to Latin-ish, then map to Unicode Braille patterns.
# This is not a full Ukrainian Braille standard implementation; it's a printable Braille-like representation.

_UA_TO_LAT = {
    'А': 'A', 'а': 'a',
    'Б': 'B', 'б': 'b',
    'В': 'V', 'в': 'v',
    'Г': 'H', 'г': 'h',
    'Ґ': 'G', 'ґ': 'g',
    'Д': 'D', 'д': 'd',
    'Е': 'E', 'е': 'e',
    'Є': 'Ye', 'є': 'ye',
    'Ж': 'Zh', 'ж': 'zh',
    'З': 'Z', 'з': 'z',
    'И': 'Y', 'и': 'y',
    'І': 'I', 'і': 'i',
    'Ї': 'Yi', 'ї': 'yi',
    'Й': 'Y', 'й': 'y',
    'К': 'K', 'к': 'k',
    'Л': 'L', 'л': 'l',
    'М': 'M', 'м': 'm',
    'Н': 'N', 'н': 'n',
    'О': 'O', 'о': 'o',
    'П': 'P', 'п': 'p',
    'Р': 'R', 'р': 'r',
    'С': 'S', 'с': 's',
    'Т': 'T', 'т': 't',
    'У': 'U', 'у': 'u',
    'Ф': 'F', 'ф': 'f',
    'Х': 'Kh', 'х': 'kh',
    'Ц': 'Ts', 'ц': 'ts',
    'Ч': 'Ch', 'ч': 'ch',
    'Ш': 'Sh', 'ш': 'sh',
    'Щ': 'Shch', 'щ': 'shch',
    'Ь': '', 'ь': '',
    'Ю': 'Yu', 'ю': 'yu',
    'Я': 'Ya', 'я': 'ya',
}

# Braille patterns for basic Latin letters a-z (Grade 1-ish), digits 0-9.
_LAT_TO_BRL = {
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽', 'z': '⠵',
    '0': '⠚', '1': '⠁', '2': '⠃', '3': '⠉', '4': '⠙', '5': '⠑',
    '6': '⠋', '7': '⠛', '8': '⠓', '9': '⠊',
    ' ': ' ',
    '.': '⠲', ',': '⠂', '?': '⠦', '!': '⠖', ':': '⠒', ';': '⠆',
    '-': '⠤', '(': '⠶', ')': '⠶',
    '\n': '\n',
}


def _to_latin(text: str) -> str:
    out = []
    for ch in text:
        out.append(_UA_TO_LAT.get(ch, ch))
    return ''.join(out)


@register.filter(name='to_braille')
def to_braille(value):
    if value is None:
        return ''
    text = str(value)
    text = _to_latin(text)

    res = []
    for ch in text:
        lower = ch.lower()
        if lower in _LAT_TO_BRL:
            res.append(_LAT_TO_BRL[lower])
        else:
            # unsupported char: keep spacing so print layout stays readable
            res.append(' ' if ch.isspace() else '⠿')
    return ''.join(res)
