document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('colors-root');
    if (!root) return;

    let items = [];
    try {
        const dataEl = document.getElementById('colors-data');
        if (dataEl && dataEl.textContent) {
            items = JSON.parse(dataEl.textContent);
        } else {
            items = JSON.parse(root.dataset.colors || '[]');
        }
    } catch {
        items = [];
    }
    if (!items.length) return;

    const nameEl = document.getElementById('color-name');
    const swatchEl = document.getElementById('color-swatch');
    const sub = document.getElementById('color-sub');
    const prev = document.getElementById('color-prev');
    const next = document.getElementById('color-next');

    let idx = 0;

    function setText(el, text) {
        if (!el) return;
        el.dataset.orig = String(text);
        el.textContent = String(text);
    }

    function reapplyBrailleIfEnabled() {
        const toggle = document.getElementById('braille-toggle');
        if (!toggle || !toggle.checked) return;
        toggle.dispatchEvent(new Event('change'));
    }

    function render() {
        const it = items[idx];
        setText(nameEl, it.name);
        if (swatchEl) swatchEl.style.background = it.hex;
        setText(sub, `Колір ${idx + 1} з ${items.length}`);
        reapplyBrailleIfEnabled();
    }

    function clamp(n) {
        if (n < 0) return 0;
        if (n >= items.length) return items.length - 1;
        return n;
    }

    if (prev) prev.addEventListener('click', () => { idx = clamp(idx - 1); render(); });
    if (next) next.addEventListener('click', () => { idx = clamp(idx + 1); render(); });

    render();
});
