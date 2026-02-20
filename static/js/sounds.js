document.addEventListener('DOMContentLoaded', () => {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    const gridEl = document.querySelector('.sounds-grid');
    let librarySounds = [];
    try {
        const raw = gridEl?.dataset?.sounds;
        if (raw) librarySounds = JSON.parse(raw);
    } catch {
        librarySounds = [];
    }

    const hasEnoughSounds = Array.isArray(librarySounds) && librarySounds.length >= 4;

    const playBtn = document.getElementById('play-btn');
    const progressEl = document.getElementById('play-progress');
    const helperBubble = document.getElementById('helper-bubble');
    const cards = Array.from(document.querySelectorAll('.sound-card'));

    if (!playBtn || !progressEl || !helperBubble || cards.length === 0) return;

    let currentTarget = null;
    let currentSet = [];
    let score = 0;
    const totalRounds = 5;
    let round = 0;
    let startTime = null;
    let firstGuessAt = null;
    let failedAttempts = 0;
    let accepting = false;

    const player = new Audio();
    player.preload = 'auto';

    const stopAllAudio = () => {
        try {
            player.pause();
            player.currentTime = 0;
        } catch {
            /* ignore */
        }
    };

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    const pickClip = (key) => {
        const item = librarySounds.find(s => String(s.id) === String(key));
        return item?.audio_url || null;
    };

    const sampleSet = () => {
        const shuffled = [...librarySounds].sort(() => Math.random() - 0.5);
        return shuffled.slice(0, 4).map(s => ({
            key: String(s.id),
            label: s.label,
            image_url: s.image_url,
        }));
    };

    const applyCards = (set) => {
        cards.forEach((card, idx) => {
            const cat = set[idx];
            if (!cat) return;
            card.dataset.sound = cat.key;
            const img = card.querySelector('.sound-card__img');
            const label = card.querySelector('.sound-card__label');
            if (img) {
                img.className = 'sound-card__img';
                img.style.backgroundImage = '';
                img.style.backgroundImage = cat.image_url ? `url('${cat.image_url}')` : '';
            }
            if (label) label.textContent = cat.label;
        });
    };

    const playClipByKey = (key) => {
        const clip = pickClip(key);
        if (!clip) return Promise.reject(new Error('no clip'));
        audioCtx.resume();
        stopAllAudio();
        player.crossOrigin = 'anonymous';
        player.src = clip;
        player.currentTime = 0;
        return player.play();
    };

    const startRound = () => {
        if (round >= totalRounds) {
            finishGame();
            return;
        }
        currentSet = sampleSet();
        currentTarget = currentSet[Math.floor(Math.random() * currentSet.length)];
        applyCards(currentSet);
        accepting = true;
        helperBubble.textContent = 'Слухай звук і натискай на картинку, яка йому відповідає.';
        playClipByKey(currentTarget.key).catch(() => {
            helperBubble.textContent = 'Не вдалося відтворити звук. Спробуй ще раз натиснути ?';
        });
    };

    const updateProgress = () => {
        progressEl.textContent = `${round}/${totalRounds}`;
    };

    const lock = () => { accepting = false; };

    const handleGuess = (key) => {
        if (!accepting) return;
        if (!firstGuessAt) firstGuessAt = Date.now();
        lock();
        stopAllAudio();
        const correct = currentTarget && key === currentTarget.key;
        if (correct) {
            score += 1;
            helperBubble.textContent = 'Правильно! Наступний звук скоро.';
        } else {
            failedAttempts += 1;
            helperBubble.textContent = 'Спробуй ще! Йдемо далі.';
        }
        round += 1;
        updateProgress();
        setTimeout(startRound, 200);
    };

    const finishGame = () => {
        accepting = false;
        stopAllAudio();
        const duration = startTime ? Date.now() - startTime : 0;
        helperBubble.textContent = `Гру завершено! Рахунок ${score}/${totalRounds}. Натисни ? щоб почати знову.`;
        const percent = Math.round((score / totalRounds) * 100);
        sendResult(percent, duration);
        startTime = null;
    };

    const startGame = () => {
        if (!hasEnoughSounds) {
            helperBubble.textContent = 'Поки що немає достатньо звуків. Спеціаліст має додати щонайменше 4 картки.';
            accepting = false;
            return;
        }
        score = 0;
        round = 0;
        firstGuessAt = null;
        failedAttempts = 0;
        updateProgress();
        helperBubble.textContent = 'Починаємо! Відтворюю перший звук.';
        startTime = Date.now();
        startRound();
    };

    const sendResult = (scoreVal, durationMs) => {
        const csrfToken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) return;
        fetch('/api/game-results/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                game_type: 'sound',
                score: scoreVal,
                duration_seconds: Math.round(durationMs / 1000),
                failed_attempts: failedAttempts,
                hesitation_time: firstGuessAt && startTime
                    ? Math.max(0, Math.floor((firstGuessAt - startTime) / 1000))
                    : 0,
            }),
        }).catch(() => {
            /* ignore network errors for now */
        });
    };

    cards.forEach(card => {
        card.addEventListener('click', () => {
            const key = card.dataset.sound;
            if (!key) return;
            // Always stop current audio immediately
            stopAllAudio();
            // Ensure game started even if user clicks card first
            if (!startTime) {
                startGame();
                return;
            }
            handleGuess(key);
        });
    });

    playBtn.addEventListener('click', () => {
        // Start a new run if finished or not started yet
        if (!startTime || round >= totalRounds) {
            startGame();
            return;
        }
        stopAllAudio();
        playClipByKey(currentTarget?.key).catch(() => {
            helperBubble.textContent = 'Не вдалося відтворити звук. Спробуй ще раз.';
        });
        updateProgress();
    });

    updateProgress();

    if (!hasEnoughSounds) {
        helperBubble.textContent = 'Поки що немає звуків для гри. Спеціаліст має додати щонайменше 4 картки.';
        cards.forEach((card) => {
            card.disabled = true;
            const label = card.querySelector('.sound-card__label');
            if (label) label.textContent = '—';
        });
        playBtn.disabled = true;
        playBtn.title = 'Додайте мінімум 4 звуки';
    }
});
