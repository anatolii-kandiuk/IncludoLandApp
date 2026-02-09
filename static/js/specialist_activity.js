document.addEventListener('DOMContentLoaded', () => {
    const root = document.querySelector('.page--activity');
    if (!root) return;

    let steps = [];
    try {
        steps = JSON.parse(root.dataset.steps || '[]');
    } catch (_e) {
        steps = [];
    }

    const imageEl = document.getElementById('activity-image');
    const imageEmpty = document.getElementById('activity-image-empty');
    const titleEl = document.getElementById('activity-title');
    const descEl = document.getElementById('activity-description');
    const taskEl = document.getElementById('activity-task');
    const audioEl = document.getElementById('activity-audio');
    const audioEmpty = document.getElementById('activity-audio-empty');
    const stepEl = document.getElementById('activity-step');
    const prevBtn = document.getElementById('activity-prev');
    const nextBtn = document.getElementById('activity-next');

    if (!steps.length) {
        if (titleEl) titleEl.textContent = 'Кроки відсутні';
        if (taskEl) taskEl.textContent = 'Спеціаліст ще не додав кроки.';
        if (prevBtn) prevBtn.disabled = true;
        if (nextBtn) nextBtn.disabled = true;
        return;
    }

    let index = 0;

    const setImage = (url) => {
        if (!imageEl || !imageEmpty) return;
        if (url) {
            imageEl.src = url;
            imageEl.style.display = 'block';
            imageEmpty.style.display = 'none';
        } else {
            imageEl.removeAttribute('src');
            imageEl.style.display = 'none';
            imageEmpty.style.display = 'grid';
        }
    };

    const setAudio = (url) => {
        if (!audioEl || !audioEmpty) return;
        if (url) {
            audioEl.src = url;
            audioEl.hidden = false;
            audioEmpty.style.display = 'none';
        } else {
            audioEl.removeAttribute('src');
            audioEl.hidden = true;
            audioEmpty.style.display = 'block';
        }
    };

    const renderStep = () => {
        const step = steps[index];
        if (!step) return;
        if (stepEl) stepEl.textContent = `Крок ${index + 1}/${steps.length}`;
        if (titleEl) titleEl.textContent = step.title || 'Крок активності';
        if (descEl) descEl.textContent = step.description || '';
        if (taskEl) taskEl.textContent = step.task_text || '';
        setImage(step.image_url || '');
        setAudio(step.audio_url || '');
        if (prevBtn) prevBtn.disabled = index === 0;
        if (nextBtn) nextBtn.textContent = index === steps.length - 1 ? 'Завершити' : 'Далі';
    };

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (index > 0) {
                index -= 1;
                renderStep();
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (index < steps.length - 1) {
                index += 1;
                renderStep();
                return;
            }
            window.location.href = '/#games';
        });
    }

    renderStep();
});
