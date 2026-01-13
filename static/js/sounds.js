document.addEventListener('DOMContentLoaded', () => {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    const soundSources = {
        forest: 'https://cdn.pixabay.com/download/audio/2021/08/08/audio_7e8e2b2c7e.mp3?filename=forest-birds-18045.mp3',
        rain: 'https://cdn.pixabay.com/download/audio/2022/03/15/audio_3f00c6c597.mp3?filename=rain-ambient-110619.mp3',
        sea: 'https://cdn.pixabay.com/download/audio/2021/11/09/audio_9f1172b4b7.mp3?filename=ocean-waves-ambient-99444.mp3',
        birds: 'https://cdn.pixabay.com/download/audio/2021/08/04/audio_5a5bcba5e5.mp3?filename=forest-birdsong-143277.mp3',
    };

    const sounds = Object.fromEntries(Object.entries(soundSources).map(([k, url]) => [k, new Audio(url)]));
    const soundKeys = Object.keys(sounds);

    const playBtn = document.getElementById('play-btn');
    const progressEl = document.getElementById('play-progress');
    const helperBubble = document.getElementById('helper-bubble');
    const cards = document.querySelectorAll('[data-sound]');

    if (!playBtn || !progressEl || !helperBubble || cards.length === 0) return;

    let queue = [];
    let current = null;
    let score = 0;
    const totalRounds = 5;
    let round = 0;
    let startTime = null;
    let accepting = false;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    const pickSound = () => soundKeys[Math.floor(Math.random() * soundKeys.length)];

    const resetQueue = () => {
        queue = Array.from({ length: totalRounds }, pickSound);
    };

    const stopAll = () => {
        Object.values(sounds).forEach(a => {
            a.pause();
            a.currentTime = 0;
        });
    };

    const playNext = () => {
        stopAll();
        if (round >= totalRounds) {
            finishGame();
            return;
        }
        current = queue[round];
        const audio = sounds[current];
        helperBubble.textContent = 'Слухай уважно і обирай, який звук почув!';
        accepting = true;
        audioCtx.resume();
        audio.currentTime = 0;
        audio.play().catch(() => {
            helperBubble.textContent = 'Не вдалося відтворити звук. Спробуй ще раз.';
        });
    };

    const updateProgress = () => {
        progressEl.textContent = `${round}/${totalRounds}`;
    };

    const lock = () => { accepting = false; };

    const handleGuess = (key) => {
        if (!accepting) return;
        lock();
        stopAll();
        const correct = key === current;
        if (correct) {
            score += 1;
            helperBubble.textContent = 'Правильно! Наступний звук скоро.';
        } else {
            helperBubble.textContent = 'Спробуй ще! Йдемо далі.';
        }
        round += 1;
        updateProgress();
        setTimeout(playNext, 900);
    };

    const finishGame = () => {
        stopAll();
        accepting = false;
        const duration = startTime ? Date.now() - startTime : 0;
        helperBubble.textContent = `Гру завершено! Рахунок ${score}/${totalRounds}. Натисни ? щоб почати знову.`;
        sendResult(score, duration);
        startTime = null;
    };

    const startGame = () => {
        stopAll();
        resetQueue();
        score = 0;
        round = 0;
        updateProgress();
        helperBubble.textContent = 'Починаємо! Відтворюю перший звук.';
        startTime = Date.now();
        setTimeout(playNext, 350);
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
                duration: durationMs,
            }),
        }).catch(() => {
            /* ignore network errors for now */
        });
    };

    cards.forEach(card => {
        card.addEventListener('click', () => handleGuess(card.dataset.sound));
    });

    playBtn.addEventListener('click', () => {
        // Start a new run if finished or not started yet
        if (!startTime || round >= totalRounds) {
            startGame();
            return;
        }
        accepting = false;
        playNext();
        updateProgress();
    });

    resetQueue();
    updateProgress();
});
