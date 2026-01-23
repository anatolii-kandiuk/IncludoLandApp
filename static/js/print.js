document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('print-now');
    const toggle = document.getElementById('braille-toggle');

    // Ukrainian Braille mapping (per Wikipedia table).
    // Note: Ґ is reported as ⠻ in older sources; Wikipedia lists ⠻.
    const CAPITAL_SIGN = '⠨';
    const NUMBER_SIGN = '⠼';

    const letterMap = {
        'А': '⠁',
        'Б': '⠃',
        'В': '⠺',
        'Г': '⠛',
        'Ґ': '⠻',
        'Д': '⠙',
        'Е': '⠑',
        'Є': '⠜',
        'Ж': '⠚',
        'З': '⠵',
        'И': '⠊',
        'І': '⠽',
        'Ї': '⠹',
        'Й': '⠯',
        'К': '⠅',
        'Л': '⠇',
        'М': '⠍',
        'Н': '⠝',
        'О': '⠕',
        'П': '⠏',
        'Р': '⠗',
        'С': '⠎',
        'Т': '⠞',
        'У': '⠥',
        'Ф': '⠋',
        'Х': '⠓',
        'Ц': '⠉',
        'Ч': '⠟',
        'Ш': '⠱',
        'Щ': '⠭',
        'Ь': '⠾',
        'Ю': '⠳',
        'Я': '⠫',
    };

    // Digits are a–j with number sign.
    const digitMap = {
        '1': '⠁',
        '2': '⠃',
        '3': '⠉',
        '4': '⠙',
        '5': '⠑',
        '6': '⠋',
        '7': '⠛',
        '8': '⠓',
        '9': '⠊',
        '0': '⠚',
    };

    const punctMap = {
        ',': '⠂',
        '.': '⠲',
        '?': '⠢',
        '!': '⠖',
        ';': '⠆',
        ':': '⠒',
        '-': '⠤',
        '’': '⠄',
        "'": '⠄',
    };

    function isUpper(ch) {
        return ch && ch === ch.toUpperCase() && ch !== ch.toLowerCase();
    }

    function toBraille(text) {
        const s = String(text || '');
        let out = '';
        let inNumber = false;

        for (let i = 0; i < s.length; i += 1) {
            const ch = s[i];

            if (digitMap[ch]) {
                if (!inNumber) {
                    out += NUMBER_SIGN;
                    inNumber = true;
                }
                out += digitMap[ch];
                continue;
            }

            // Break number mode on non-digit
            inNumber = false;

            if (punctMap[ch]) {
                out += punctMap[ch];
                continue;
            }

            const up = ch.toUpperCase();
            if (Object.prototype.hasOwnProperty.call(letterMap, up)) {
                if (isUpper(ch)) out += CAPITAL_SIGN;
                out += letterMap[up];
                continue;
            }

            // preserve spaces and other symbols
            out += ch;
        }

        return out;
    }

    function setBrailleEnabled(enabled) {
        document.body.classList.toggle('is-braille', Boolean(enabled));

        const nodes = document.querySelectorAll('[data-braille]');
        nodes.forEach((el) => {
            if (!el) return;
            if (!el.dataset.orig) {
                el.dataset.orig = el.textContent || '';
            }
            el.textContent = enabled ? toBraille(el.dataset.orig) : el.dataset.orig;
        });
    }

    if (toggle) {
        toggle.addEventListener('change', () => {
            setBrailleEnabled(Boolean(toggle.checked));
        });
    }

    if (btn) {
        btn.addEventListener('click', () => {
            if (toggle) setBrailleEnabled(Boolean(toggle.checked));
            window.print();
        });
    }
});
