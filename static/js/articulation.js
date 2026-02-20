document.addEventListener('DOMContentLoaded', () => {
    const shell = document.querySelector('.art-shell');
    const navItems = Array.from(document.querySelectorAll('.art-nav__item'));
    const imageEl = document.getElementById('art-image');
    const titleEl = document.getElementById('art-title');
    const instructionEl = document.getElementById('art-instruction');
    const countEl = document.getElementById('art-count');
    const startBtn = document.getElementById('art-start');
    const doneBtn = document.getElementById('art-done');
    const ratingWrap = document.getElementById('art-rating');
    const ratingButtons = Array.from(document.querySelectorAll('.art-star'));
    const nextImageBtn = document.getElementById('art-next-image');
    const msgEl = document.getElementById('art-msg');

    if (!shell || !imageEl || !titleEl || !instructionEl || !countEl || !startBtn || !doneBtn || !ratingWrap || !nextImageBtn || !msgEl) return;

    let cards = [];
    const dataEl = document.getElementById('articulation-cards-data');
    if (dataEl) {
        try {
            cards = JSON.parse(dataEl.textContent || '[]');
        } catch (_e) {
            cards = [];
        }
    }

    let current = null;
    let currentImages = [];
    let currentImageIndex = 0;
    let startedAt = null;
    let firstActionAt = null;
    let completed = 0;
    let currentStreak = 0;
    let maxStreak = 0;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function setMessage(text) {
        msgEl.textContent = text;
    }

    function setActiveButton(cardId) {
        navItems.forEach((btn) => {
            const active = String(btn.dataset.cardId) === String(cardId);
            btn.classList.toggle('is-active', active);
        });
    }

    function applyCard(card) {
        if (!card) return;
        current = card;
        titleEl.textContent = card.title || 'Вправа';
        instructionEl.textContent = card.instruction || 'Виконуй вправу у комфортному темпі.';
        currentImages = Array.isArray(card.images) && card.images.length
            ? card.images
            : (card.image_url ? [card.image_url] : []);
        currentImageIndex = 0;
        if (currentImages.length) {
            imageEl.style.backgroundImage = `url('${currentImages[0]}')`;
        } else {
            imageEl.style.backgroundImage = '';
        }
        imageEl.classList.toggle('has-image', Boolean(currentImages.length));
        nextImageBtn.hidden = currentImages.length <= 1;
        setActiveButton(card.id);
    }

    function showNextImage() {
        if (!currentImages.length) return;
        currentImageIndex = (currentImageIndex + 1) % currentImages.length;
        imageEl.style.backgroundImage = `url('${currentImages[currentImageIndex]}')`;
    }

    function selectCard(cardId) {
        if (startedAt) {
            setMessage('Спершу завершіть поточну вправу.');
            return;
        }
        const card = cards.find((c) => String(c.id) === String(cardId));
        if (!card) return;
        applyCard(card);
        setMessage('Натисни "Почати вправу", коли готовий.');
    }

    function setButtons(mode) {
        const isRunning = mode === 'running';
        const isAwaitingRating = mode === 'awaiting_rating';

        startBtn.disabled = isRunning || isAwaitingRating;
        doneBtn.hidden = !isRunning;
        ratingWrap.hidden = !isAwaitingRating;
    }

    function updateRatingHighlight(stars) {
        ratingButtons.forEach((btn) => {
            const buttonRating = Number(btn.dataset.rating || '0');
            btn.classList.toggle('is-active', buttonRating <= stars);
        });
    }

    async function sendResult({ score, rawScore, maxScore, ratingStars, durationSeconds, failedAttempts, hesitationTime, sessionMaxStreak }) {
        const csrfToken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) return;
        try {
            await fetch('/api/game-results/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    game_type: 'articulation',
                    score,
                    raw_score: rawScore,
                    max_score: maxScore,
                    duration_seconds: durationSeconds,
                    failed_attempts: failedAttempts,
                    hesitation_time: hesitationTime,
                    max_streak: sessionMaxStreak,
                    details: {
                        card_id: current?.id,
                        card_title: current?.title,
                        rating_stars: ratingStars,
                        successful_attempts: rawScore,
                    },
                }),
            });
        } catch (_e) {
            /* ignore */
        }
    }

    function startExercise() {
        if (!cards.length) {
            setMessage('Поки що немає карток для вправ.');
            return;
        }
        if (!current) {
            applyCard(cards[0]);
        }
        startedAt = Date.now();
        firstActionAt = null;
        setButtons('running');
        setMessage('Чудово! Виконуй вправу, а потім натисни "Завершити".');
    }

    function finishExercise() {
        if (!startedAt) return;
        if (!firstActionAt) firstActionAt = Date.now();
        updateRatingHighlight(0);
        setButtons('awaiting_rating');
        setMessage('Оціни виконання вправи від 1 до 5 зірок.');
    }

    function completeWithRating(ratingStars) {
        if (!startedAt) return;
        const stars = Math.max(1, Math.min(5, Number(ratingStars || 0)));
        const endedAt = Date.now();
        const durationSeconds = Math.max(1, Math.round((endedAt - startedAt) / 1000));
        const hesitationTime = Math.max(0, Math.round(((firstActionAt || endedAt) - startedAt) / 1000));
        const score = stars * 20;
        const failedAttempts = 5 - stars;

        if (stars >= 3) {
            currentStreak += 1;
            maxStreak = Math.max(maxStreak, currentStreak);
        } else {
            currentStreak = 0;
        }

        updateRatingHighlight(stars);

        sendResult({
            score,
            rawScore: stars,
            maxScore: 5,
            ratingStars: stars,
            durationSeconds,
            failedAttempts,
            hesitationTime,
            sessionMaxStreak: maxStreak,
        });

        startedAt = null;
        firstActionAt = null;
        completed += 1;
        countEl.textContent = String(completed);
        setButtons('idle');
        setMessage('Результат збережено. Можеш обрати наступну вправу.');
    }

    navItems.forEach((btn) => {
        btn.addEventListener('click', () => {
            selectCard(btn.dataset.cardId);
        });
    });

    startBtn.addEventListener('click', startExercise);
    doneBtn.addEventListener('click', finishExercise);
    ratingButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            completeWithRating(btn.dataset.rating);
        });
    });
    nextImageBtn.addEventListener('click', showNextImage);

    if (!cards.length) {
        startBtn.disabled = true;
        setMessage('Поки що немає вправ. Спеціаліст має додати картки.');
        return;
    }

    setButtons('idle');

    if (navItems.length) {
        selectCard(navItems[0].dataset.cardId);
    } else if (cards.length) {
        applyCard(cards[0]);
    }
});
