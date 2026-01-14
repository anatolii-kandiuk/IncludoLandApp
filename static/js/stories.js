(() => {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function decodeEscapedText(value) {
        if (!value) return '';
        return String(value)
            .replace(/\\r\\n/g, '\n')
            .replace(/\\n/g, '\n')
            .replace(/\\r/g, '\n')
            .replace(/\\t/g, '\t');
    }

    async function postListen(storyId, durationSeconds) {
        const csrftoken = getCookie('csrftoken');
        if (!csrftoken) return;
        try {
            await fetch('/api/story-listens/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                body: JSON.stringify({
                    story_id: storyId,
                    duration_seconds: durationSeconds ?? null,
                }),
                credentials: 'same-origin',
            });
        } catch {
            // ignore
        }
    }

    window.addEventListener('DOMContentLoaded', () => {
        const modal = document.getElementById('story-modal');
        const modalTitle = document.getElementById('story-modal-title');
        const modalContent = document.getElementById('story-modal-content');
        const audio = document.getElementById('story-audio');

        if (!audio) return;

        let currentStoryId = null;
        let startedAt = 0;

        function openModal(title, text) {
            if (!modal || !modalTitle || !modalContent) return;
            modalTitle.textContent = title || 'Казка';
            modalContent.textContent = text || '';
            modal.classList.remove('modal--hidden');
        }

        function closeModal() {
            if (!modal) return;
            modal.classList.add('modal--hidden');
        }

        if (modal) {
            modal.addEventListener('click', (e) => {
                const target = e.target;
                const action = target?.getAttribute?.('data-action') || target?.closest?.('[data-action]')?.getAttribute?.('data-action');
                if (action === 'close') closeModal();
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });

        function stopAudio() {
            try {
                audio.pause();
                audio.currentTime = 0;
            } catch {
                // ignore
            }
        }

        document.querySelectorAll('.story-card').forEach((card) => {
            card.addEventListener('click', async (e) => {
                const btn = e.target?.closest?.('[data-action]');
                if (!btn) return;

                const action = btn.getAttribute('data-action');
                const storyId = Number(card.dataset.storyId);
                const title = card.dataset.title || '';
                const text = decodeEscapedText(card.dataset.text || '');
                const audioUrl = card.dataset.audioUrl || '';

                if (action === 'read') {
                    openModal(title, text || 'Текст недоступний.');
                    return;
                }

                if (action === 'listen') {
                    if (!audioUrl) return;
                    stopAudio();

                    currentStoryId = storyId;
                    startedAt = Date.now();
                    audio.src = audioUrl;
                    audio.play().catch(() => { /* ignore */ });
                }
            });
        });

        audio.addEventListener('ended', async () => {
            if (!currentStoryId || !startedAt) return;
            const durationSeconds = Math.max(0, Math.round((Date.now() - startedAt) / 1000));
            const storyId = currentStoryId;
            currentStoryId = null;
            startedAt = 0;
            await postListen(storyId, durationSeconds);
        });

        audio.addEventListener('pause', () => {
            // reset when user manually stops
            if (audio.currentTime === 0) {
                currentStoryId = null;
                startedAt = 0;
            }
        });
    });
})();
