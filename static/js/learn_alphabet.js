document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('alphabet-root');
    if (!root) return;

    let letters = [];
    const dataEl = document.getElementById('alphabet-data');
    try {
        if (dataEl && dataEl.textContent) {
            letters = JSON.parse(dataEl.textContent);
        } else {
            letters = JSON.parse(root.dataset.letters || '[]');
        }
    } catch {
        letters = [];
    }
    if (!letters.length) return;

    const big = document.getElementById('alpha-big');
    const sub = document.getElementById('alpha-sub');
    const prev = document.getElementById('alpha-prev');
    const next = document.getElementById('alpha-next');
    const idxEl = document.getElementById('alpha-idx');

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
        const it = letters[idx];
        setText(big, `${it.upper} ${it.lower}`);
        setText(sub, `Буква ${idx + 1} з ${letters.length}`);
        if (idxEl) idxEl.textContent = String(idx + 1);
        reapplyBrailleIfEnabled();
    }

    function clamp(n) {
        if (n < 0) return 0;
        if (n >= letters.length) return letters.length - 1;
        return n;
    }

    if (prev) {
        prev.addEventListener('click', () => {
            idx = clamp(idx - 1);
            render();
        });
    }

    if (next) {
        next.addEventListener('click', () => {
            idx = clamp(idx + 1);
            render();
        });
    }

    render();
});
