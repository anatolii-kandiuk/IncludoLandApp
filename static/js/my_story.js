document.addEventListener('DOMContentLoaded', () => {
    const page = document.querySelector('.page--my-story');
    const imageEl = document.getElementById('story-image');
    const textEl = document.getElementById('story-text');
    const saveBtn = document.getElementById('story-save');
    const nextBtn = document.getElementById('story-next');
    const msgEl = document.getElementById('story-msg');

    if (!page || !imageEl || !textEl || !saveBtn || !nextBtn || !msgEl) return;

    let images = [];
    try {
        images = JSON.parse(page.dataset.images || '[]');
    } catch (_e) {
        images = [];
    }

    let current = null;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

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
            saveBtn.disabled = true;
            nextBtn.disabled = true;
            return;
        }
        imageEl.style.backgroundImage = img.image_url ? `url('${img.image_url}')` : '';
        imageEl.classList.toggle('has-image', Boolean(img.image_url));
        setMessage('Опиши, що відбувається на картинці.');
        saveBtn.disabled = false;
        nextBtn.disabled = images.length <= 1;
    }

    async function saveStory() {
        const text = (textEl.value || '').trim();
        if (!text) {
            setMessage('Напиши кілька речень про свою історію.');
            return;
        }
        const csrfToken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) {
            setMessage('Не вдалося зберегти. Онови сторінку.');
            return;
        }
        try {
            const res = await fetch('/api/my-stories/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    text,
                    image_id: current?.id || null,
                }),
            });
            if (!res.ok) throw new Error('bad status');
            setMessage('Казку збережено! Можеш написати ще одну.');
            textEl.value = '';
            if (images.length > 1) {
                const next = pickRandom(current?.id);
                applyImage(next);
            }
        } catch (_e) {
            setMessage('Не вдалося зберегти. Спробуй ще раз.');
        }
    }

    saveBtn.addEventListener('click', saveStory);
    nextBtn.addEventListener('click', () => {
        const next = pickRandom(current?.id);
        applyImage(next);
    });

    applyImage(pickRandom());
});
