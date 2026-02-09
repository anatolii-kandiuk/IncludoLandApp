document.addEventListener('DOMContentLoaded', () => {
    const page = document.querySelector('.page--my-story');
    const imageEl = document.getElementById('story-image');
    const nextBtn = document.getElementById('story-next');
    const msgEl = document.getElementById('story-msg');

    if (!page || !imageEl || !nextBtn || !msgEl) return;

    let images = [];
    try {
        images = JSON.parse(page.dataset.images || '[]');
    } catch (_e) {
        images = [];
    }

    let current = null;

    function setMessage(text) {
        msgEl.textContent = text;
    }

    function pickRandom(exceptId) {
        if (!images.length) return null;
        if (images.length === 1) return images[0];
        let next = images[Math.floor(Math.random() * images.length)];
        if (exceptId) {
            let guard = 0;
            while (String(next.id) === String(exceptId) && guard < 6) {
                next = images[Math.floor(Math.random() * images.length)];
                guard += 1;
            }
        }
        return next;
    }

    function applyImage(img) {
        current = img;
        if (!img) {
            imageEl.style.backgroundImage = '';
            imageEl.classList.remove('has-image');
            setMessage('Поки що немає картинок. Спеціаліст має додати зображення.');
            nextBtn.disabled = true;
            return;
        }
        imageEl.style.backgroundImage = img.image_url ? `url('${img.image_url}')` : '';
        imageEl.classList.toggle('has-image', Boolean(img.image_url));
        setMessage('Розкажи вголос, що відбувається на картинці.');
        nextBtn.disabled = images.length <= 1;
    }
    nextBtn.addEventListener('click', () => {
        const next = pickRandom(current?.id);
        applyImage(next);
    });

    applyImage(pickRandom());
});
