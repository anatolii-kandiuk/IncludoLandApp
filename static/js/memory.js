(() => {
    const grid = document.getElementById('memory-grid');
    if (!grid) return;

    const msgEl = document.getElementById('memory-msg');
    const counterEl = document.getElementById('memory-counter');
    const totalEl = document.getElementById('memory-total');

    const totalPairs = Number(grid.dataset.pairs || '6');
    if (totalEl) totalEl.textContent = String(totalPairs);

    const icons = [
        {
            id: 'sun',
            label: 'Сонце',
            svg: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="#fff"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M4.3 4.3l1.8 1.8M17.9 17.9l1.8 1.8M19.7 4.3l-1.8 1.8M6.1 17.9l-1.8 1.8" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>',
        },
        {
            id: 'moon',
            label: 'Місяць',
            svg: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15.5 3.2c-2.1 1-3.6 3.2-3.6 5.8 0 3.5 2.9 6.4 6.4 6.4 1.2 0 2.3-.3 3.3-.9-.9 3.6-4.1 6.3-8 6.3-4.6 0-8.3-3.7-8.3-8.3 0-4 2.7-7.3 6.4-8.1.9-.2 2.2-.4 3.8-.2z" fill="#fff"/></svg>',
        },
        {
            id: 'star',
            label: 'Зірка',
            svg: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8l2.8 6 6.5.6-4.9 4.2 1.5 6.3-5.9-3.5-5.9 3.5 1.5-6.3-4.9-4.2 6.5-.6 2.8-6z" fill="#fff"/></svg>',
        },
        {
            id: 'heart',
            label: 'Серце',
            svg: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-9.2-9.1C1.6 8 3.6 5.8 6.2 5.8c1.8 0 3.1 1 3.8 2 0 0 1-2 4-2 2.7 0 4.8 2.2 3.4 5.6C19.5 15.9 12 20.5 12 20.5z" fill="#fff"/></svg>',
        },
        {
            id: 'leaf',
            label: 'Листок',
            svg: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4c-6.5 0-12 3-14.5 7.5C3.5 15 6 19.5 10.6 20c4.2.5 8.5-2.5 10.6-7.7.7-1.7.9-3.3.9-4.8 0-1.2-.2-2.3-.6-3.5z" fill="#fff"/><path d="M8.2 18c2.6-3.1 6.6-6.1 11.8-8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>',
        },
        {
            id: 'music',
            label: 'Нота',
            svg: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4v11.2c0 2-1.6 3.6-3.6 3.6S6.8 17.2 6.8 15.2s1.6-3.6 3.6-3.6c.7 0 1.3.2 1.8.5V6.2L20 4v4.6l-6 1.3" fill="#fff"/></svg>',
        },
    ].slice(0, totalPairs);

    const deck = shuffle([
        ...icons.map((i) => ({ ...i, key: `${i.id}-a` })),
        ...icons.map((i) => ({ ...i, key: `${i.id}-b` })),
    ]);

    let first = null;
    let second = null;
    let locked = false;
    let matchedPairs = 0;
    let sessionStartedAt = Date.now();
    let startedAt = null;
    let firstFlipAt = null;
    let failedAttempts = 0;
    let currentStreak = 0;
    let maxStreak = 0;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    async function postResult(payload) {
        try {
            const csrf = getCookie('csrftoken');
            const res = await fetch('/api/game-results/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrf ? { 'X-CSRFToken': csrf } : {}),
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });
            return res.ok;
        } catch (_e) {
            return false;
        }
    }

    function computeScore(timeSec, pairs) {
        // Score 0..100 (higher is better). For 6 pairs: ~100 at 20s, ~60 at 40s, ~20 at 60s.
        const baseline = 18 + pairs * 2;
        const penaltyPerSec = 2;
        const raw = Math.round(100 - Math.max(0, timeSec - baseline) * penaltyPerSec);
        return Math.max(0, Math.min(100, raw));
    }

    function setMsg(text) {
        if (msgEl) msgEl.textContent = text;
    }

    function setCounter(value) {
        if (counterEl) counterEl.textContent = String(value);
    }

    function makeCard(card) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'memory-card';
        btn.dataset.id = card.id;
        btn.dataset.key = card.key;
        btn.dataset.state = 'hidden';
        btn.setAttribute('aria-label', `Картка: ${card.label}`);
        btn.setAttribute('aria-pressed', 'false');

        btn.innerHTML = `
      <div class="card">
        <div class="card__face card__back" aria-hidden="true">
          <div class="card__circle"><div class="card__q">?</div></div>
        </div>
        <div class="card__face card__front" aria-hidden="true">
          <div class="card__circle"><div class="card__icon">${card.svg}</div></div>
        </div>
      </div>
    `;

        btn.addEventListener('click', () => onFlip(btn));
        return btn;
    }

    function onFlip(btn) {
        if (locked) return;
        if (btn.dataset.state === 'matched') return;
        if (btn.dataset.state === 'flipped') return;

        if (!startedAt) startedAt = Date.now();
        if (!firstFlipAt) firstFlipAt = Date.now();

        btn.dataset.state = 'flipped';
        btn.setAttribute('aria-pressed', 'true');

        if (!first) {
            first = btn;
            setMsg('Добре! Тепер знайди пару.');
            return;
        }

        second = btn;
        locked = true;

        const isMatch = first.dataset.id === second.dataset.id;
        if (isMatch) {
            first.dataset.state = 'matched';
            second.dataset.state = 'matched';
            first.disabled = true;
            second.disabled = true;

            matchedPairs += 1;
            setCounter(matchedPairs);
            setMsg(matchedPairs === totalPairs ? 'Молодець! Усі пари знайдено.' : 'Супер! Пара знайдена.');

            if (matchedPairs === totalPairs) {
                const timeSec = startedAt ? Math.floor((Date.now() - startedAt) / 1000) : 0;
                const score = computeScore(timeSec, totalPairs);
                postResult({
                    game_type: 'memory',
                    score,
                    raw_score: totalPairs,
                    max_score: totalPairs,
                    duration_seconds: timeSec,
                    failed_attempts: failedAttempts,
                    hesitation_time: Math.max(0, Math.floor(((firstFlipAt || Date.now()) - sessionStartedAt) / 1000)),
                    max_streak: maxStreak,
                    details: {
                        pairs: totalPairs,
                    },
                });
            }

            currentStreak += 1;
            maxStreak = Math.max(maxStreak, currentStreak);

            first = null;
            second = null;
            locked = false;
            return;
        }

        setMsg('Не пара. Спробуй ще!');
        failedAttempts += 1;
        currentStreak = 0;
        window.setTimeout(() => {
            if (first) {
                first.dataset.state = 'hidden';
                first.setAttribute('aria-pressed', 'false');
            }
            if (second) {
                second.dataset.state = 'hidden';
                second.setAttribute('aria-pressed', 'false');
            }
            first = null;
            second = null;
            locked = false;
        }, 750);
    }

    function shuffle(arr) {
        const a = arr.slice();
        for (let i = a.length - 1; i > 0; i -= 1) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    // Render
    grid.innerHTML = '';
    deck.forEach((c) => grid.appendChild(makeCard(c)));
    setCounter(0);
    setMsg('Зосередься!');
})();
