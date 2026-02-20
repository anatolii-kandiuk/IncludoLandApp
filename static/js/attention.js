document.addEventListener('DOMContentLoaded', () => {
    const leftCard = document.getElementById('left-card');
    const rightCard = document.getElementById('right-card');
    const hotspots = document.getElementById('hotspots');
    const overlay = document.getElementById('diff-overlay');
    const dotsEl = document.getElementById('dots');
    const progressText = document.getElementById('progress-text');
    const helperMsg = document.getElementById('helper-msg');
    const dataEl = document.getElementById('attention-data');
    const leftScene = leftCard ? leftCard.querySelector('.scene') : null;
    const rightScene = rightCard ? rightCard.querySelector('.scene') : null;

    const refreshBtn = document.getElementById('att-refresh');
    const nextBtn = document.getElementById('att-next');
    const levelEl = document.getElementById('att-level');
    const shapesEl = document.getElementById('att-shapes');
    const missesEl = document.getElementById('att-misses');

    if (!leftCard || !rightCard || !hotspots || !overlay || !dotsEl || !progressText || !helperMsg || !dataEl || !leftScene || !rightScene) return;

    let data;
    try {
        data = JSON.parse(dataEl.textContent || '{}');
    } catch (e) {
        // Bad payload should not break the page.
        data = {};
    }

    const initialTargets = Array.isArray(data.targets) ? data.targets : [];
    const total = Number.isFinite(data.total) ? data.total : 5;
    const storageKey = 'attention_level';
    let level = Number.parseInt(window.localStorage.getItem(storageKey) || String(data.level || 1), 10);
    if (!Number.isFinite(level) || level < 1) level = 1;

    if (!initialTargets.length) {
        helperMsg.textContent = 'Немає даних для гри. Оновіть сторінку.';
        progressText.textContent = '0/0';
        return;
    }

    const state = {
        found: new Set(),
        total,
        misses: 0,
        currentStreak: 0,
        maxStreak: 0,
    };

    let levelStartedAt = Date.now();
    let firstClickAt = null;
    let resultPosted = false;

    const MAX_MISSES = 3;

    let targets = initialTargets;
    let targetById = new Map();
    let diffMarkById = new Map();

    const updateProgress = () => {
        progressText.textContent = `${state.found.size}/${state.total}`;
        dotsEl.querySelectorAll('.dot').forEach((dot, idx) => {
            dot.classList.toggle('active', idx < state.found.size);
        });
    };

    const setMessage = (text) => {
        helperMsg.textContent = text;
    };

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    async function postResult(payload) {
        try {
            const csrf = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
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

    function maybeMarkFirstClick() {
        if (!firstClickAt) firstClickAt = Date.now();
    }

    function buildResultPayload(completed) {
        const now = Date.now();
        const durationSeconds = Math.max(1, Math.round((now - levelStartedAt) / 1000));
        const hesitationTime = Math.max(0, Math.round(((firstClickAt || now) - levelStartedAt) / 1000));
        const foundCount = state.found.size;
        const foundScore = state.total ? Math.round((foundCount * 100) / state.total) : 0;
        const missPenalty = state.misses * 10;
        const score = completed
            ? Math.max(0, Math.min(100, 100 - missPenalty))
            : Math.max(0, Math.min(100, foundScore - missPenalty));

        return {
            game_type: 'attention',
            score,
            raw_score: foundCount,
            max_score: state.total,
            duration_seconds: durationSeconds,
            failed_attempts: state.misses,
            hesitation_time: hesitationTime,
            max_streak: state.maxStreak,
            details: {
                level,
                shapes_count: Number(shapesEl?.textContent || 0) || null,
                completed,
            },
        };
    }

    function sendLevelResult(completed) {
        if (resultPosted) return;
        resultPosted = true;
        postResult(buildResultPayload(completed));
    }

    const updateMisses = () => {
        if (!missesEl) return;
        missesEl.textContent = `${state.misses}/${MAX_MISSES}`;
    };

    const percent = (value, max) => `${(value * 100) / max}%`;

    const showMiss = (clientX, clientY) => {
        const rect = rightCard.getBoundingClientRect();
        if (!rect.width || !rect.height) return;

        const x = ((clientX - rect.left) / rect.width) * 100;
        const y = ((clientY - rect.top) / rect.height) * 100;
        if (x < 0 || x > 100 || y < 0 || y > 100) return;

        const miss = document.createElement('span');
        miss.className = 'miss-mark';
        miss.style.left = `${x}%`;
        miss.style.top = `${y}%`;
        overlay.appendChild(miss);
        window.setTimeout(() => {
            miss.remove();
        }, 550);
    };

    const onMiss = () => {
        if (state.misses >= MAX_MISSES) return;
        maybeMarkFirstClick();
        state.currentStreak = 0;
        state.misses += 1;
        updateMisses();

        if (state.misses < MAX_MISSES) return;

        sendLevelResult(false);

        // Go back one difficulty step (levels are grouped by 3).
        const downgradedLevel = Math.max(1, level - 3);
        if (downgradedLevel === level) {
            setMessage('3 промахи — спробуй ще раз на цьому рівні.');
        } else {
            level = downgradedLevel;
            window.localStorage.setItem(storageKey, String(level));
            if (levelEl) levelEl.textContent = String(level);
            setMessage('3 промахи — повертаємось на легший рівень.');
        }

        // Small delay so the child can read the message.
        window.setTimeout(() => {
            loadLevel(level);
        }, 500);
    };

    const onFound = (id) => {
        state.found.add(id);
        updateProgress();
        if (state.found.size === state.total) {
            sendLevelResult(true);
            setMessage('Молодець! Рівень пройдено. Натисни «Наступний рівень».');
            rightCard.classList.add('is-complete');
            if (nextBtn) nextBtn.hidden = false;
        } else {
            setMessage('Є ще відмінності, шукай далі!');
        }
    };

    const renderDots = () => {
        dotsEl.innerHTML = '';
        for (let i = 0; i < state.total; i += 1) {
            const dot = document.createElement('span');
            dot.className = 'dot';
            dotsEl.appendChild(dot);
        }
    };

    const applyMeta = (payload) => {
        if (levelEl) levelEl.textContent = String(payload.level || level);
        if (shapesEl) shapesEl.textContent = String(payload.shapes_count || '');
    };

    const resetLevelState = () => {
        state.found = new Set();
        state.misses = 0;
        state.currentStreak = 0;
        state.maxStreak = 0;
        levelStartedAt = Date.now();
        firstClickAt = null;
        resultPosted = false;
        rightCard.classList.remove('is-complete');
        if (nextBtn) nextBtn.hidden = true;
        updateProgress();
        updateMisses();
    };

    const renderTargets = () => {
        hotspots.innerHTML = '';
        overlay.innerHTML = '';
        targetById = new Map();
        diffMarkById = new Map();

        // Create marks only for correct targets (diffs).
        const diffs = targets.filter((t) => Boolean(t && t.is_diff));
        diffs.forEach((t, index) => {
            const spotId = String(t.id || index);
            const xPct = percent(Number(t.x || 0), 200);
            const yPct = percent(Number(t.y || 0), 120);
            const mark = document.createElement('span');
            mark.className = 'diff-mark';
            mark.style.left = xPct;
            mark.style.top = yPct;
            mark.dataset.id = spotId;
            overlay.appendChild(mark);
            diffMarkById.set(spotId, mark);
        });

        // All shapes are clickable.
        targets.forEach((t, index) => {
            const targetId = String(t.id || index);
            const xPct = percent(Number(t.x || 0), 200);
            const yPct = percent(Number(t.y || 0), 120);

            targetById.set(targetId, t);

            const btn = document.createElement('button');
            btn.className = 'hotspot';
            btn.type = 'button';
            btn.style.left = xPct;
            btn.style.top = yPct;
            btn.dataset.id = targetId;
            btn.setAttribute('aria-label', `Фігура ${index + 1}`);

            btn.addEventListener('click', (ev) => {
                ev.stopPropagation();
                if (state.found.size === state.total) return;
                maybeMarkFirstClick();

                const info = targetById.get(targetId);
                if (!info) return;

                if (info.is_diff) {
                    if (state.found.has(targetId)) return;
                    btn.classList.add('found');
                    state.currentStreak += 1;
                    state.maxStreak = Math.max(state.maxStreak, state.currentStreak);
                    const mark = diffMarkById.get(targetId);
                    if (mark) mark.classList.add('revealed');
                    onFound(targetId);
                } else {
                    setMessage('Не тут 🙂 Спробуй ще!');
                    state.currentStreak = 0;
                    // Show miss marker centered on the clicked shape.
                    const miss = document.createElement('span');
                    miss.className = 'miss-mark';
                    miss.style.left = xPct;
                    miss.style.top = yPct;
                    overlay.appendChild(miss);
                    window.setTimeout(() => miss.remove(), 550);
                    onMiss();
                }
            });

            hotspots.appendChild(btn);
        });
    };

    const applyLevelPayload = (payload) => {
        if (!payload) return;
        if (Number.isFinite(payload.level) && payload.level >= 1) {
            level = payload.level;
            window.localStorage.setItem(storageKey, String(level));
            if (levelEl) levelEl.textContent = String(level);
        }
        if (payload.left_svg) leftScene.innerHTML = payload.left_svg;
        if (payload.right_svg) rightScene.innerHTML = payload.right_svg;

        targets = Array.isArray(payload.targets) ? payload.targets : [];
        resetLevelState();
        renderDots();
        renderTargets();
        applyMeta(payload);
        setMessage('Порівняй картинки та натискай на відмінності праворуч.');
    };

    const fetchLevel = async (lvl) => {
        const url = `/games/attention/?json=1&level=${encodeURIComponent(String(lvl))}`;
        const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    };

    const loadLevel = async (lvl) => {
        setMessage('Завантажую рівень...');
        try {
            const payload = await fetchLevel(lvl);
            applyLevelPayload(payload);
        } catch (e) {
            setMessage('Не вдалося завантажити рівень. Спробуй Refresh.');
        }
    };

    rightCard.addEventListener('click', (ev) => {
        if (state.found.size === state.total) return;
        maybeMarkFirstClick();
        // If click wasn't captured by a hotspot, it's a miss.
        setMessage('Не тут 🙂 Спробуй ще!');
        showMiss(ev.clientX, ev.clientY);
        onMiss();
    });

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadLevel(level);
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            level += 1;
            window.localStorage.setItem(storageKey, String(level));
            loadLevel(level);
        });
    }

    renderDots();
    renderTargets();
    updateProgress();
    updateMisses();
    if (levelEl) levelEl.textContent = String(level);
    window.localStorage.setItem(storageKey, String(level));
    // Always sync to stored level without a full page reload.
    loadLevel(level);
});
