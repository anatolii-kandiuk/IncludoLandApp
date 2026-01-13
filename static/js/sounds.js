document.addEventListener('DOMContentLoaded', () => {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    const categories = [
        {
            key: 'forest',
            label: 'Ліс',
            bg: 'sound-card__img--forest',
            clips: [
                'https://cdn.pixabay.com/download/audio/2021/08/08/audio_7e8e2b2c7e.mp3?filename=forest-birds-18045.mp3',
                'https://cdn.pixabay.com/download/audio/2022/05/02/audio_e7e95ee128.mp3?filename=forest-ambient-11252.mp3',
            ],
        },
        {
            key: 'rain',
            label: 'Дощ',
            bg: 'sound-card__img--rain',
            clips: [
                'https://cdn.pixabay.com/download/audio/2022/03/15/audio_3f00c6c597.mp3?filename=rain-ambient-110619.mp3',
                'https://cdn.pixabay.com/download/audio/2021/09/07/audio_b115c9a27c.mp3?filename=rain-and-thunder-6899.mp3',
            ],
        },
        {
            key: 'sea',
            label: 'Море',
            bg: 'sound-card__img--sea',
            clips: [
                'https://cdn.pixabay.com/download/audio/2021/11/09/audio_9f1172b4b7.mp3?filename=ocean-waves-ambient-99444.mp3',
                'https://cdn.pixabay.com/download/audio/2021/09/07/audio_34098dd31b.mp3?filename=ocean-waves-ambience-6201.mp3',
            ],
        },
        {
            key: 'birds',
            label: 'Птахи',
            bg: 'sound-card__img--birds',
            clips: [
                'https://cdn.pixabay.com/download/audio/2021/08/04/audio_5a5bcba5e5.mp3?filename=forest-birdsong-143277.mp3',
                'https://cdn.pixabay.com/download/audio/2021/11/16/audio_9d7db33629.mp3?filename=spring-birds-singing-ambient-113325.mp3',
            ],
        },
        {
            key: 'fire',
            label: 'Вогнище',
            bg: 'sound-card__img--fire',
            clips: [
                'https://cdn.pixabay.com/download/audio/2021/08/04/audio_4b97e67f4f.mp3?filename=campfire-crackling-113842.mp3',
            ],
        },
        {
            key: 'city',
            label: 'Місто',
            bg: 'sound-card__img--city',
            clips: [
                'https://cdn.pixabay.com/download/audio/2021/09/07/audio_de123dc57b.mp3?filename=city-traffic-ambience-6200.mp3',
            ],
        },
        {
            key: 'night',
            label: 'Ніч',
            bg: 'sound-card__img--night',
            clips: [
                'https://cdn.pixabay.com/download/audio/2021/08/04/audio_9e8261e1a0.mp3?filename=night-ambience-12833.mp3',
            ],
        },
        {
            key: 'river',
            label: 'Річка',
            bg: 'sound-card__img--river',
            clips: [
                'https://cdn.pixabay.com/download/audio/2021/08/08/audio_83f2b30b2d.mp3?filename=river-ambience-19797.mp3',
            ],
        },
    ];

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
    let accepting = false;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    const pickClip = (key) => {
        const cat = categories.find(c => c.key === key);
        if (!cat || !cat.clips.length) return null;
        return cat.clips[Math.floor(Math.random() * cat.clips.length)];
    };

    const sampleSet = () => {
        const shuffled = [...categories].sort(() => Math.random() - 0.5);
        return shuffled.slice(0, 4);
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
                img.classList.add(cat.bg);
            }
            if (label) label.textContent = cat.label;
        });
    };

    const playClipByKey = (key) => {
        const clip = pickClip(key);
        if (!clip) return Promise.reject(new Error('no clip'));
        const audio = new Audio(clip);
        audio.crossOrigin = 'anonymous';
        audioCtx.resume();
        audio.currentTime = 0;
        return audio.play();
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
        lock();
        const correct = currentTarget && key === currentTarget.key;
        if (correct) {
            score += 1;
            helperBubble.textContent = 'Правильно! Наступний звук скоро.';
        } else {
            helperBubble.textContent = 'Спробуй ще! Йдемо далі.';
        }
        round += 1;
        updateProgress();
        setTimeout(startRound, 900);
    };

    const finishGame = () => {
        accepting = false;
        const duration = startTime ? Date.now() - startTime : 0;
        helperBubble.textContent = `Гру завершено! Рахунок ${score}/${totalRounds}. Натисни ? щоб почати знову.`;
        const percent = Math.round((score / totalRounds) * 100);
        sendResult(percent, duration);
        startTime = null;
    };

    const startGame = () => {
        score = 0;
        round = 0;
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
            }),
        }).catch(() => {
            /* ignore network errors for now */
        });
    };

    cards.forEach(card => {
        card.addEventListener('click', () => {
            const key = card.dataset.sound;
            if (!key) return;
            // Ensure game started even if user clicks card first
            if (!startTime) {
                startGame();
                return;
            }
            playClipByKey(key).catch(() => {
                helperBubble.textContent = 'Не вдалося відтворити звук цієї картки.';
            });
            handleGuess(key);
        });
    });

    playBtn.addEventListener('click', () => {
        // Start a new run if finished or not started yet
        if (!startTime || round >= totalRounds) {
            startGame();
            return;
        }
        playClipByKey(currentTarget?.key).catch(() => {
            helperBubble.textContent = 'Не вдалося відтворити звук. Спробуй ще раз.';
        });
        updateProgress();
    });

    updateProgress();
});
