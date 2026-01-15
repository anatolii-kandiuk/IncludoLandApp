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

    function downloadTextFile(filename, text) {
        const blob = new Blob([text ?? ''], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
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
        let currentAudioHref = '';

        function normalizeUrl(url) {
            if (!url) return '';
            try {
                return new URL(url, window.location.href).href;
            } catch {
                return String(url);
            }
        }

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
            currentAudioHref = '';
        }

        function syncCardAudioButtons(card, isPlaying) {
            const listenBtn = card.querySelector('[data-action="listen"]');
            const pauseBtn = card.querySelector('[data-action="pause"]');
            if (!pauseBtn) return;

            if (!card.dataset.audioUrl) {
                pauseBtn.disabled = true;
                return;
            }

            pauseBtn.disabled = false;
            if (isPlaying) {
                pauseBtn.textContent = '⏸ Пауза';
                pauseBtn.dataset.state = 'playing';
                if (listenBtn) listenBtn.disabled = false;
            } else {
                pauseBtn.textContent = '▶ Продовжити';
                pauseBtn.dataset.state = 'paused';
                if (listenBtn) listenBtn.disabled = false;
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

                if (action === 'download-text') {
                    if (!text) return;
                    const safeTitle = (title || 'kazka').replace(/[\\/:*?"<>|]+/g, '_');
                    downloadTextFile(`${safeTitle}.txt`, text);
                    return;
                }

                if (action === 'read') {
                    openModal(title, text || 'Текст недоступний.');
                    return;
                }

                if (action === 'listen') {
                    if (!audioUrl) return;
                    stopAudio();

                    currentStoryId = storyId;
                    startedAt = Date.now();
                    currentAudioHref = normalizeUrl(audioUrl);
                    audio.src = currentAudioHref;
                    audio.play().catch(() => { /* ignore */ });

                    // enable pause button on this card
                    syncCardAudioButtons(card, true);
                }

                if (action === 'pause') {
                    if (!audioUrl) return;
                    const requestedHref = normalizeUrl(audioUrl);
                    if (currentAudioHref !== requestedHref) {
                        // If another story is loaded, start this one instead.
                        stopAudio();
                        currentStoryId = storyId;
                        startedAt = Date.now();
                        currentAudioHref = requestedHref;
                        audio.src = currentAudioHref;
                        audio.play().catch(() => { /* ignore */ });
                        syncCardAudioButtons(card, true);
                        return;
                    }

                    if (audio.paused) {
                        audio.play().catch(() => { /* ignore */ });
                        syncCardAudioButtons(card, true);
                    } else {
                        audio.pause();
                        syncCardAudioButtons(card, false);
                    }
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

            // reset pause buttons
            document.querySelectorAll('.story-card').forEach((card) => {
                if (Number(card.dataset.storyId) === storyId) {
                    syncCardAudioButtons(card, false);
                }
            });
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
