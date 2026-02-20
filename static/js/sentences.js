document.addEventListener('DOMContentLoaded', () => {
    const totalEl = document.getElementById('sent-total');
    const roundEl = document.getElementById('sent-round');
    const timeEl = document.getElementById('sent-time');
    const emojiEl = document.getElementById('sent-emoji');
    const promptEl = document.getElementById('sent-prompt');
    const pickedEl = document.getElementById('sent-picked');
    const bankEl = document.getElementById('sent-bank');
    const msgEl = document.getElementById('sent-msg');
    const clearBtn = document.getElementById('sent-clear');
    const startBtn = document.getElementById('sent-start');
    const checkBtn = document.getElementById('sent-check');
    const cardEl = document.querySelector('.sentences-card');

    if (!totalEl || !roundEl || !timeEl || !emojiEl || !promptEl || !pickedEl || !bankEl || !msgEl || !clearBtn || !startBtn || !checkBtn || !cardEl) {
        return;
    }

    const DEFAULT_EXERCISES = [
        { prompt: 'Склади речення про котика', sentence: 'Кіт спить на дивані.', emoji: '🐱' },
        { prompt: 'Склади речення про сонце', sentence: 'Сонце світить у небі.', emoji: '☀️' },
        { prompt: 'Склади речення про дощ', sentence: 'Дощ капає з хмар.', emoji: '🌧️' },
        { prompt: 'Склади речення про маму', sentence: 'Мама читає мені казку.', emoji: '📖' },
        { prompt: 'Склади речення про ліс', sentence: 'У лісі співають пташки.', emoji: '🌲' },
    ];

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function setState(state) {
        cardEl.dataset.state = state || '';
    }

    function parseExercisesFromDom() {
        const raw = cardEl?.dataset?.sentences;
        if (!raw) return [];
        try {
            const arr = JSON.parse(raw);
            if (!Array.isArray(arr)) return [];
            return arr
                .map((it) => ({
                    id: it.id,
                    prompt: String(it.prompt || '').trim(),
                    sentence: String(it.sentence || '').trim(),
                    emoji: String(it.emoji || '').trim() || '🧩',
                }))
                .filter((it) => it.prompt && it.sentence);
        } catch {
            return [];
        }
    }

    function shuffle(arr) {
        const a = [...arr];
        for (let i = a.length - 1; i > 0; i -= 1) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    function tokenize(sentence) {
        return sentence
            .split(/\s+/)
            .map((t) => t.trim())
            .filter(Boolean);
    }

    function normalizeText(text) {
        return String(text || '').trim().replace(/\s+/g, ' ');
    }

    const EXERCISES = parseExercisesFromDom();
    const POOL = EXERCISES.length ? EXERCISES : DEFAULT_EXERCISES;
    const MAX_ROUNDS = 5;
    const TOTAL_ROUNDS = Math.min(MAX_ROUNDS, POOL.length);
    totalEl.textContent = String(TOTAL_ROUNDS);

    let round = 0;
    let correct = 0;
    let startTime = null;
    let firstActionAt = null;
    let failedAttempts = 0;
    let currentStreak = 0;
    let maxStreak = 0;
    let timerId = null;

    let runExercises = [];
    let current = null;

    let bankTokens = [];
    let pickedTokens = [];

    function updateTimer() {
        if (!startTime) {
            timeEl.textContent = '0';
            return;
        }
        const seconds = Math.floor((Date.now() - startTime) / 1000);
        timeEl.textContent = String(seconds);
    }

    function stopTimer() {
        if (timerId) window.clearInterval(timerId);
        timerId = null;
    }

    function startTimer() {
        stopTimer();
        timerId = window.setInterval(updateTimer, 250);
        updateTimer();
    }

    function makeTokenObjects(tokens) {
        return tokens.map((text, idx) => ({ id: `${idx}-${Math.random().toString(16).slice(2)}`, text }));
    }

    function renderContainer(containerEl, items, origin) {
        containerEl.innerHTML = '';
        items.forEach((tok) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'sent-pill';
            btn.textContent = tok.text;
            btn.dataset.id = tok.id;
            btn.dataset.origin = origin;
            btn.draggable = true;

            btn.addEventListener('click', () => {
                if (origin === 'bank') moveToken(tok.id, 'bank', 'picked');
                else moveToken(tok.id, 'picked', 'bank');
            });

            btn.addEventListener('dragstart', (e) => {
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', JSON.stringify({ id: tok.id, from: origin }));
            });

            btn.addEventListener('dragover', (e) => {
                // allow drop reordering
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            });

            btn.addEventListener('drop', (e) => {
                e.preventDefault();
                let payload;
                try {
                    payload = JSON.parse(e.dataTransfer.getData('text/plain') || '{}');
                } catch {
                    payload = {};
                }
                if (!payload?.id || !payload?.from) return;

                const to = origin;
                if (payload.from === to && to === 'picked') {
                    // reorder within picked
                    reorderPicked(payload.id, tok.id);
                    return;
                }

                if (payload.from === 'bank' && to === 'picked') {
                    moveToken(payload.id, 'bank', 'picked', { beforeId: tok.id });
                    return;
                }

                if (payload.from === 'picked' && to === 'bank') {
                    moveToken(payload.id, 'picked', 'bank');
                }
            });

            containerEl.appendChild(btn);
        });
    }

    function findAndRemove(list, id) {
        const idx = list.findIndex((t) => t.id === id);
        if (idx === -1) return null;
        return list.splice(idx, 1)[0];
    }

    function moveToken(id, from, to, opts = {}) {
        const source = from === 'bank' ? bankTokens : pickedTokens;
        const dest = to === 'bank' ? bankTokens : pickedTokens;

        if (!firstActionAt && from === 'bank' && to === 'picked') {
            firstActionAt = Date.now();
        }

        const token = findAndRemove(source, id);
        if (!token) return;

        if (to === 'picked' && opts.beforeId) {
            const beforeIdx = dest.findIndex((t) => t.id === opts.beforeId);
            if (beforeIdx >= 0) dest.splice(beforeIdx, 0, token);
            else dest.push(token);
        } else {
            dest.push(token);
        }

        render();
        setState('');
    }

    function reorderPicked(moveId, beforeId) {
        const token = findAndRemove(pickedTokens, moveId);
        if (!token) return;
        const idx = pickedTokens.findIndex((t) => t.id === beforeId);
        if (idx < 0) {
            pickedTokens.push(token);
        } else {
            pickedTokens.splice(idx, 0, token);
        }
        render();
    }

    function render() {
        renderContainer(pickedEl, pickedTokens, 'picked');
        renderContainer(bankEl, bankTokens, 'bank');
    }

    function resetRoundUi() {
        setState('');
        msgEl.textContent = 'Перетягуй або натискай слова, щоб скласти речення.';
        pickedTokens = [];
        bankTokens = [];
        render();
    }

    function setRoundExercise(item) {
        current = item;
        emojiEl.textContent = item.emoji || '🧩';
        promptEl.textContent = item.prompt;

        const tokens = tokenize(item.sentence);
        const tokenObjects = makeTokenObjects(tokens);
        bankTokens = shuffle(tokenObjects);
        pickedTokens = [];
        render();
        setState('');
    }

    function nextRound() {
        if (round >= TOTAL_ROUNDS) {
            finish();
            return;
        }
        roundEl.textContent = String(round + 1);
        setRoundExercise(runExercises[round]);
    }

    function checkAnswer() {
        if (!current) return;
        const guess = normalizeText(pickedTokens.map((t) => t.text).join(' '));
        const target = normalizeText(current.sentence);

        if (!guess) {
            setState('wrong');
            msgEl.textContent = 'Склади речення зі слів.';
            return;
        }

        if (guess === target) {
            correct += 1;
            currentStreak += 1;
            maxStreak = Math.max(maxStreak, currentStreak);
            setState('correct');
            msgEl.textContent = 'Правильно!';
            window.setTimeout(() => {
                round += 1;
                nextRound();
            }, 700);
        } else {
            failedAttempts += 1;
            currentStreak = 0;
            setState('wrong');
            msgEl.textContent = 'Не зовсім. Спробуй ще раз!';
        }
    }

    function clearPicked() {
        if (!pickedTokens.length) return;
        bankTokens = shuffle([...bankTokens, ...pickedTokens]);
        pickedTokens = [];
        render();
        setState('');
        msgEl.textContent = 'Очищено.';
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

    function finish() {
        stopTimer();
        const durationMs = startTime ? (Date.now() - startTime) : 0;
        const score = TOTAL_ROUNDS ? Math.round((correct * 100) / TOTAL_ROUNDS) : 0;

        setState(correct === TOTAL_ROUNDS ? 'correct' : '');
        msgEl.textContent = `Готово! Правильно: ${correct}/${TOTAL_ROUNDS}.`;

        postResult({
            game_type: 'sentences',
            score,
            raw_score: correct,
            max_score: TOTAL_ROUNDS,
            duration_seconds: Math.round(durationMs / 1000),
            failed_attempts: failedAttempts,
            hesitation_time: firstActionAt && startTime
                ? Math.max(0, Math.floor((firstActionAt - startTime) / 1000))
                : 0,
            max_streak: maxStreak,
            details: {
                rounds: TOTAL_ROUNDS,
            },
        });

        current = null;
    }

    function start() {
        if (!TOTAL_ROUNDS) {
            msgEl.textContent = 'Поки що немає речень для гри.';
            return;
        }
        runExercises = shuffle(POOL).slice(0, TOTAL_ROUNDS);
        round = 0;
        correct = 0;
        failedAttempts = 0;
        currentStreak = 0;
        maxStreak = 0;
        firstActionAt = null;
        startTime = Date.now();
        startTimer();
        nextRound();
    }

    // Allow dropping directly onto containers
    function setupDropZone(containerEl, zone) {
        containerEl.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });
        containerEl.addEventListener('drop', (e) => {
            e.preventDefault();
            let payload;
            try {
                payload = JSON.parse(e.dataTransfer.getData('text/plain') || '{}');
            } catch {
                payload = {};
            }
            if (!payload?.id || !payload?.from) return;

            if (payload.from === zone) return;
            moveToken(payload.id, payload.from, zone);
        });
    }

    setupDropZone(pickedEl, 'picked');
    setupDropZone(bankEl, 'bank');

    startBtn.addEventListener('click', start);
    clearBtn.addEventListener('click', clearPicked);
    checkBtn.addEventListener('click', checkAnswer);

    // Initial UI
    resetRoundUi();
});
