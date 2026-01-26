(() => {
    const KEY = 'includoland_pomodoro_v1';

    const DEFAULTS = {
        mode: 'work', // work | break
        running: false,
        remainingSec: 25 * 60,
        lastTickMs: null,
        workSec: 25 * 60,
        breakSec: 5 * 60,
        startedOnce: false,
    };

    function safeParse(json) {
        try {
            return JSON.parse(json);
        } catch (_e) {
            return null;
        }
    }

    function loadState() {
        const raw = window.localStorage.getItem(KEY);
        const parsed = raw ? safeParse(raw) : null;
        if (!parsed || typeof parsed !== 'object') return { ...DEFAULTS };

        const st = { ...DEFAULTS, ...parsed };
        if (!['work', 'break'].includes(st.mode)) st.mode = 'work';
        st.running = Boolean(st.running);
        st.remainingSec = Math.max(0, Math.min(24 * 60 * 60, parseInt(st.remainingSec, 10) || 0));
        st.lastTickMs = typeof st.lastTickMs === 'number' ? st.lastTickMs : null;
        st.workSec = Math.max(60, Math.min(60 * 180, parseInt(st.workSec, 10) || DEFAULTS.workSec));
        st.breakSec = Math.max(60, Math.min(60 * 60, parseInt(st.breakSec, 10) || DEFAULTS.breakSec));
        st.startedOnce = Boolean(st.startedOnce);
        return st;
    }

    function saveState(st) {
        window.localStorage.setItem(KEY, JSON.stringify(st));
    }

    function pad2(n) {
        return String(n).padStart(2, '0');
    }

    function formatTime(sec) {
        const s = Math.max(0, sec);
        const m = Math.floor(s / 60);
        const r = s % 60;
        return `${pad2(m)}:${pad2(r)}`;
    }

    function nextMode(st) {
        const mode = st.mode === 'work' ? 'break' : 'work';
        const remainingSec = mode === 'work' ? st.workSec : st.breakSec;
        return { ...st, mode, remainingSec, running: false, lastTickMs: null };
    }

    function applyElapsed(st, nowMs, onModeSwitch) {
        if (!st.running) return st;
        if (!st.lastTickMs) return { ...st, lastTickMs: nowMs };

        const elapsedSec = Math.floor((nowMs - st.lastTickMs) / 1000);
        if (elapsedSec <= 0) return st;

        let remaining = st.remainingSec - elapsedSec;
        if (remaining <= 0) {
            // flip mode when timer ends
            const prevMode = st.mode;
            const switched = nextMode({ ...st, remainingSec: 0, running: false, lastTickMs: null });
            saveState(switched);
            if (typeof onModeSwitch === 'function') {
                onModeSwitch(prevMode, switched.mode);
            }
            return switched;
        }

        return { ...st, remainingSec: remaining, lastTickMs: nowMs };
    }

    function bindUI() {
        const pill = document.getElementById('timer-pill');
        const pillTime = document.getElementById('timer-pill-time');
        const popover = document.getElementById('timer-popover');
        if (!pill || !pillTime || !popover) return;

        const closeBtn = document.getElementById('timer-close');
        const timeEl = document.getElementById('timer-time');
        const modeEl = document.getElementById('timer-mode');
        const startBtn = document.getElementById('timer-start');
        const pauseBtn = document.getElementById('timer-pause');
        const resetBtn = document.getElementById('timer-reset');
        const toast = document.getElementById('timer-toast');
        const toastText = document.getElementById('timer-toast-text');
        const toastClose = document.getElementById('timer-toast-close');

        let state = loadState();
        let intervalId = null;
        let toastTimeoutId = null;

        function showToast(message) {
            if (!toast || !toastText) return;

            // If some logic triggers the same toast repeatedly, don't keep extending it forever.
            if (!toast.hidden && toastText.textContent === message && toastTimeoutId) {
                return;
            }

            toastText.textContent = message;
            toast.hidden = false;
            if (toastTimeoutId) window.clearTimeout(toastTimeoutId);
            toastTimeoutId = window.setTimeout(() => {
                toast.hidden = true;
                toastTimeoutId = null;
            }, 8000);
        }

        function hideToast() {
            if (!toast) return;
            toast.hidden = true;
            if (toastTimeoutId) {
                window.clearTimeout(toastTimeoutId);
                toastTimeoutId = null;
            }
        }

        function onModeSwitch(prevMode, newMode) {
            if (prevMode === 'work' && newMode === 'break') {
                showToast('Пора відпочити');
            } else if (prevMode === 'break' && newMode === 'work') {
                showToast('Пора до роботи');
            }
        }

        function render() {
            const nowMs = Date.now();
            state = applyElapsed(state, nowMs, onModeSwitch);
            saveState(state);

            const t = formatTime(state.remainingSec);
            pillTime.textContent = t;
            pill.title = state.mode === 'work' ? 'Робота' : 'Перерва';

            if (timeEl) timeEl.textContent = t;
            if (modeEl) modeEl.textContent = state.mode === 'work' ? 'Робота' : 'Перерва';

            if (startBtn) {
                startBtn.textContent = state.running ? 'Йде…' : 'Старт';
                startBtn.disabled = state.running;
            }
            if (pauseBtn) pauseBtn.disabled = !state.running;
        }

        function startTicking() {
            if (intervalId) return;
            intervalId = window.setInterval(render, 250);
        }

        function stopTicking() {
            if (!intervalId) return;
            window.clearInterval(intervalId);
            intervalId = null;
        }

        function open() {
            popover.hidden = false;
            pill.setAttribute('aria-expanded', 'true');
            hideToast();
        }

        function close() {
            popover.hidden = true;
            pill.setAttribute('aria-expanded', 'false');
        }

        function start() {
            const nowMs = Date.now();
            state = applyElapsed(state, nowMs, onModeSwitch);
            state.running = true;
            state.lastTickMs = nowMs;
            state.startedOnce = true;
            saveState(state);
            render();
        }

        function pause() {
            const nowMs = Date.now();
            state = applyElapsed(state, nowMs, onModeSwitch);
            state.running = false;
            state.lastTickMs = null;
            saveState(state);
            render();
        }

        function reset() {
            state = { ...state, running: false, lastTickMs: null };
            state.remainingSec = state.mode === 'work' ? state.workSec : state.breakSec;
            state.startedOnce = true;
            saveState(state);
            render();
        }

        // Auto-start once for kids when they open the app.
        if (!state.startedOnce) {
            const nowMs = Date.now();
            state.mode = 'work';
            state.remainingSec = state.workSec;
            state.running = true;
            state.lastTickMs = nowMs;
            state.startedOnce = true;
            saveState(state);
        }

        // Always tick to keep navbar time updated.
        startTicking();

        pill.addEventListener('click', () => {
            if (popover.hidden) open();
            else close();
        });

        closeBtn?.addEventListener('click', close);
        toastClose?.addEventListener('click', hideToast);
        toast?.addEventListener('click', () => {
            hideToast();
            open();
        });

        document.addEventListener('click', (e) => {
            const target = e.target;
            if (!(target instanceof Node)) return;
            if (popover.hidden) return;
            if (popover.contains(target) || pill.contains(target)) return;
            close();
        });

        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !popover.hidden) close();
        });

        startBtn?.addEventListener('click', start);
        pauseBtn?.addEventListener('click', pause);
        resetBtn?.addEventListener('click', reset);

        render();
    }

    window.addEventListener('DOMContentLoaded', bindUI);
})();
