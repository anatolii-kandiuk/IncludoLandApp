(() => {
    const TOTAL = 10;

    const els = {
        level: document.getElementById('math-level'),
        op: document.getElementById('math-op'),
        levelPill: document.getElementById('math-level-pill'),
        opPill: document.getElementById('math-op-pill'),
        start: document.getElementById('math-start'),
        best: document.getElementById('math-best'),
        time: document.getElementById('math-time'),
        step: document.getElementById('math-step'),
        total: document.getElementById('math-total'),
        progressFill: document.getElementById('math-progress-fill'),
        expression: document.getElementById('math-expression'),
        answer: document.getElementById('math-answer'),
        submit: document.getElementById('math-submit'),
        msg: document.getElementById('math-msg'),
        levelDots: Array.from(document.querySelectorAll('.hud__dots span[data-level]')),
    };

    if (!els.start) return;

    const storageKey = 'includoland_math_best_v1';

    const LEVELS = ['easy', 'medium', 'hard'];
    const OPS = ['mix', 'add', 'sub', 'mul', 'div'];
    const LEVEL_LABEL = { easy: 'Легко', medium: 'Середньо', hard: 'Складно' };
    const OP_LABEL = { mix: 'Мікс', add: '+', sub: '−', mul: '×', div: '÷' };

    const state = {
        active: false,
        step: 0,
        correct: 0,
        current: null,
        timerId: null,
        startedAt: 0,
        firstActionAt: 0,
        failedAttempts: 0,
        currentStreak: 0,
        maxStreak: 0,
    };

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

    function clamp(n, min, max) {
        return Math.max(min, Math.min(max, n));
    }

    function randInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    function pick(arr) {
        return arr[randInt(0, arr.length - 1)];
    }

    function readBest() {
        const raw = localStorage.getItem(storageKey);
        const n = Number(raw);
        return Number.isFinite(n) ? clamp(n, 0, TOTAL) : 0;
    }

    function writeBest(v) {
        localStorage.setItem(storageKey, String(clamp(v, 0, TOTAL)));
    }

    function setMsg(text, kind) {
        els.msg.textContent = text;
        els.msg.dataset.kind = kind || '';
    }

    function setControlsEnabled(enabled) {
        els.answer.disabled = !enabled;
        els.submit.disabled = !enabled;
    }

    function updateHud() {
        els.step.textContent = String(state.step);
        const pct = state.step === 0 ? 0 : Math.round((state.step / TOTAL) * 100);
        if (els.progressFill && els.progressFill.style) {
            els.progressFill.style.width = `${pct}%`;
        }
    }

    function syncLevelDots() {
        if (!els.levelDots || !els.levelDots.length) return;
        const current = els.level?.value;
        els.levelDots.forEach((dot) => {
            const match = dot.dataset.level === current;
            dot.classList.toggle('is-active', Boolean(match));
        });
    }

    function syncPills() {
        if (els.total) els.total.textContent = String(TOTAL);
        if (els.levelPill) {
            els.levelPill.textContent = `Рівень: ${LEVEL_LABEL[els.level.value] || 'Легко'}`;
        }
        if (els.opPill) {
            els.opPill.textContent = `Операція: ${OP_LABEL[els.op.value] || 'Мікс'}`;
        }
        syncLevelDots();
    }

    function cycleSelect(selectEl, order) {
        const idx = order.indexOf(selectEl.value);
        const next = order[(idx + 1 + order.length) % order.length];
        selectEl.value = next;
        selectEl.dispatchEvent(new Event('change', { bubbles: true }));
        syncPills();
    }

    function opSymbol(op) {
        if (op === 'add') return '+';
        if (op === 'sub') return '−';
        if (op === 'mul') return '×';
        if (op === 'div') return '÷';
        return '?';
    }

    function allowedOpsForLevel(level) {
        if (level === 'hard') return new Set(['mul', 'div']);
        return new Set(['add', 'sub']);
    }

    function normalizeSettings() {
        const level = els.level.value;
        const allowed = allowedOpsForLevel(level);

        // Disable incompatible operations in the <select>.
        if (els.op) {
            Array.from(els.op.options).forEach((opt) => {
                if (opt.value === 'mix') {
                    opt.disabled = false;
                    return;
                }
                opt.disabled = !allowed.has(opt.value);
            });
        }

        // Coerce op to something valid for this level.
        if (els.op.value !== 'mix' && !allowed.has(els.op.value)) {
            els.op.value = 'mix';
        }
    }

    function generateProblem(level, opMode) {
        // Level rules per request:
        // - easy: digits 0..9
        // - medium: 10..100
        // - hard: multiplication & division (integer-only)
        const allowedSet = allowedOpsForLevel(level);
        const allowed = opMode === 'mix' ? Array.from(allowedSet) : [opMode];
        const op = allowedSet.has(allowed[0]) ? allowed[0] : pick(Array.from(allowedSet));

        let a;
        let b;
        let answer;

        if (level === 'easy') {
            a = randInt(0, 9);
            b = randInt(0, 9);

            if (op === 'sub' && b > a) [a, b] = [b, a];
            answer = op === 'add' ? a + b : a - b;
        } else if (level === 'medium') {
            a = randInt(10, 100);
            b = randInt(10, 100);

            if (op === 'sub' && b > a) [a, b] = [b, a];
            answer = op === 'add' ? a + b : a - b;
        } else {
            // hard
            if (op === 'div') {
                const divisor = randInt(2, 12);
                const quotient = randInt(2, 12);
                a = divisor * quotient;
                b = divisor;
                answer = quotient;
            } else {
                a = randInt(2, 12);
                b = randInt(2, 12);
                answer = a * b;
            }
        }

        const text = `${a} ${opSymbol(op)} ${b} = ?`;
        return { a, b, op, answer, text };
    }

    function tick() {
        const sec = Math.floor((Date.now() - state.startedAt) / 1000);
        els.time.textContent = String(sec);
    }

    function startTimer() {
        stopTimer();
        state.startedAt = Date.now();
        tick();
        state.timerId = window.setInterval(tick, 250);
    }

    function stopTimer() {
        if (state.timerId) {
            window.clearInterval(state.timerId);
            state.timerId = null;
        }
    }

    function nextQuestion() {
        normalizeSettings();
        const level = els.level.value;
        const opMode = els.op.value;
        state.current = generateProblem(level, opMode);

        els.expression.textContent = state.current.text;
        els.answer.value = '';
        els.answer.focus();

        setMsg('Введи відповідь і натисни “Перевірити”.', '');
    }

    function finishGame() {
        state.active = false;
        setControlsEnabled(false);
        stopTimer();

        const prevBest = readBest();
        if (state.correct > prevBest) {
            writeBest(state.correct);
        }
        els.best.textContent = String(readBest());

        const timeSec = Math.floor((Date.now() - state.startedAt) / 1000);
        const hesitationSec = state.firstActionAt
            ? Math.max(0, Math.floor((state.firstActionAt - state.startedAt) / 1000))
            : timeSec;
        setMsg(`Готово! Результат: ${state.correct}/${TOTAL}. Час: ${timeSec}с.`, 'done');

        els.expression.textContent = 'Натисни “Почати”,\nщоб зіграти ще раз';

        const score = TOTAL > 0 ? Math.round((state.correct / TOTAL) * 100) : 0;
        postResult({
            game_type: 'math',
            score,
            raw_score: state.correct,
            max_score: TOTAL,
            duration_seconds: timeSec,
            failed_attempts: state.failedAttempts,
            hesitation_time: hesitationSec,
            max_streak: state.maxStreak,
            details: {
                level: els.level?.value,
                op: els.op?.value,
            },
        });
    }

    function submitAnswer() {
        if (!state.active || !state.current) return;
        if (!state.firstActionAt) state.firstActionAt = Date.now();

        const raw = els.answer.value.trim();
        if (!raw) {
            setMsg('Спочатку введи відповідь.', 'warn');
            return;
        }

        const value = Number(raw);
        const ok = value === state.current.answer;

        state.step += 1;
        if (ok) {
            state.correct += 1;
            state.currentStreak += 1;
            state.maxStreak = Math.max(state.maxStreak, state.currentStreak);
            setMsg('Правильно! Так тримати!', 'ok');
        } else {
            state.failedAttempts += 1;
            state.currentStreak = 0;
            setMsg(`Майже! Правильна відповідь: ${state.current.answer}`, 'bad');
        }

        updateHud();

        window.setTimeout(() => {
            if (state.step >= TOTAL) {
                finishGame();
            } else {
                nextQuestion();
            }
        }, 650);
    }

    function startGame() {
        normalizeSettings();
        state.active = true;
        state.step = 0;
        state.correct = 0;
        state.current = null;
        state.firstActionAt = 0;
        state.failedAttempts = 0;
        state.currentStreak = 0;
        state.maxStreak = 0;

        els.best.textContent = String(readBest());
        els.time.textContent = '0';

        setControlsEnabled(true);
        updateHud();
        startTimer();
        nextQuestion();
    }

    els.best.textContent = String(readBest());
    normalizeSettings();
    syncPills();

    els.start.addEventListener('click', startGame);
    els.submit.addEventListener('click', submitAnswer);
    els.answer.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') submitAnswer();
    });

    // If user changes settings mid-game, restart.
    els.level.addEventListener('change', () => {
        normalizeSettings();
        syncPills();
        if (!state.active) return;
        setMsg('Налаштування змінено — починаю заново.', 'warn');
        startGame();
    });
    els.op.addEventListener('change', () => {
        normalizeSettings();
        syncPills();
        if (!state.active) return;
        setMsg('Налаштування змінено — починаю заново.', 'warn');
        startGame();
    });

    if (els.levelPill) {
        els.levelPill.addEventListener('click', () => cycleSelect(els.level, LEVELS));
    }
    if (els.opPill) {
        els.opPill.addEventListener('click', () => cycleSelect(els.op, OPS));
    }
})();
