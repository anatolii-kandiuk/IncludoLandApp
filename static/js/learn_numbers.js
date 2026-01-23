document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('numbers-root');
    if (!root) return;

    let items = [];
    try {
        const dataEl = document.getElementById('numbers-data');
        if (dataEl && dataEl.textContent) {
            items = JSON.parse(dataEl.textContent);
        } else {
            items = JSON.parse(root.dataset.numbers || '[]');
        }
    } catch {
        items = [];
    }
    if (!items.length) return;

    const big = document.getElementById('num-big');
    const sub = document.getElementById('num-sub');
    const bigDots = document.getElementById('num-dots');
    const prev = document.getElementById('num-prev');
    const next = document.getElementById('num-next');

    let idx = 0;

    function setText(el, text) {
        if (!el) return;
        el.dataset.orig = String(text);
        el.textContent = String(text);
    }

    function renderDots(container, n) {
        if (!container) return;
        const val = Math.max(0, Math.min(10, Number(n)));
        container.innerHTML = '';
        for (let i = 0; i < val; i += 1) {
            const d = document.createElement('span');
            d.className = 'num-dot';
            container.appendChild(d);
        }
    }

    function reapplyBrailleIfEnabled() {
        const toggle = document.getElementById('braille-toggle');
        if (!toggle || !toggle.checked) return;
        toggle.dispatchEvent(new Event('change'));
    }

    function render() {
        const it = items[idx];
        setText(big, String(it.n));
        if (big) big.dataset.n = String(it.n);
        setText(sub, `Цифра ${idx + 1} з ${items.length}`);
        renderDots(bigDots, it.n);
        reapplyBrailleIfEnabled();
    }

    function clamp(n) {
        if (n < 0) return 0;
        if (n >= items.length) return items.length - 1;
        return n;
    }

    if (prev) prev.addEventListener('click', () => { idx = clamp(idx - 1); render(); });
    if (next) next.addEventListener('click', () => { idx = clamp(idx + 1); render(); });

    // Render dot counters inside the grid.
    document.querySelectorAll('.grid-item[data-n]').forEach((card) => {
        const n = card.getAttribute('data-n');
        const dots = card.querySelector('.num-dots');
        renderDots(dots, n);
    });

    render();
});
