document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('print-now');
    const toggle = document.getElementById('braille-toggle');

    const BRAILLE_PREFIX = '⠈';
    const map = {
        'А': '⠁',
        'Б': '⠃',
        'В': '⠺',
        'Г': '⠛',
        'Д': '⠙',
        'Е': '⠑',
        'Ж': '⠚',
        'З': '⠵',
        'И': '⠊',
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

        // Ukrainian-specific letters (approximated as base+prefix)
        'І': BRAILLE_PREFIX + '⠊',
        'Ї': BRAILLE_PREFIX + BRAILLE_PREFIX + '⠊',
        'Є': BRAILLE_PREFIX + '⠑',
        'Ґ': BRAILLE_PREFIX + '⠛',
    };

    function toBraille(text) {
        const s = String(text || '');
        let out = '';
        for (let i = 0; i < s.length; i += 1) {
            const ch = s[i];
            const up = ch.toUpperCase();
            if (Object.prototype.hasOwnProperty.call(map, up)) {
                out += map[up];
            } else {
                out += ch;
            }
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
