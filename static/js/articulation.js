document.addEventListener('DOMContentLoaded', () => {
    const shell = document.querySelector('.art-shell');
    const navItems = Array.from(document.querySelectorAll('.art-nav__item'));
    const imageEl = document.getElementById('art-image');
    const titleEl = document.getElementById('art-title');
    const instructionEl = document.getElementById('art-instruction');
    const countEl = document.getElementById('art-count');
    const startBtn = document.getElementById('art-start');
    const doneBtn = document.getElementById('art-done');
    const successBtn = document.getElementById('art-success');
    const failBtn = document.getElementById('art-fail');
    const nextImageBtn = document.getElementById('art-next-image');
    const msgEl = document.getElementById('art-msg');

    if (!shell || !imageEl || !titleEl || !instructionEl || !countEl || !startBtn || !doneBtn || !successBtn || !failBtn || !nextImageBtn || !msgEl) return;

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
        const isAwaitingOutcome = mode === 'awaiting_outcome';

        startBtn.disabled = isRunning || isAwaitingOutcome;
        doneBtn.hidden = !isRunning;
        successBtn.hidden = !isAwaitingOutcome;
        failBtn.hidden = !isAwaitingOutcome;
    }

    async function sendResult({ score, durationSeconds, outcome, failedAttempts, hesitationTime }) {
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
                    raw_score: outcome === 'success' ? 1 : 0,
                    max_score: 1,
                    duration_seconds: durationSeconds,
                    failed_attempts: failedAttempts,
                    hesitation_time: hesitationTime,
                    details: {
                        card_id: current?.id,
                        card_title: current?.title,
                        outcome,
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
        setButtons('awaiting_outcome');
        setMessage('Оціни виконання вправи: обери "Вийшло" або "Не вийшло".');
    }

    function completeWithOutcome(outcome) {
        if (!startedAt) return;
        const endedAt = Date.now();
        const durationSeconds = Math.max(1, Math.round((endedAt - startedAt) / 1000));
        const hesitationTime = Math.max(0, Math.round(((firstActionAt || endedAt) - startedAt) / 1000));
        const isSuccess = outcome === 'success';

        sendResult({
            score: isSuccess ? 100 : 0,
            durationSeconds,
            outcome,
            failedAttempts: isSuccess ? 0 : 1,
            hesitationTime,
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
    successBtn.addEventListener('click', () => completeWithOutcome('success'));
    failBtn.addEventListener('click', () => completeWithOutcome('failed'));
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
