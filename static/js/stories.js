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

        const player = document.getElementById('audio-player');
        const playerTitle = document.getElementById('audio-player-title');
        const playerToggle = document.getElementById('audio-player-toggle');
        const seek = document.getElementById('audio-seek');
        const currentTimeEl = document.getElementById('audio-current');
        const durationEl = document.getElementById('audio-duration');

        if (!audio) return;

        let currentStoryId = null;
        let startedAt = 0;
        let currentAudioHref = '';
        let currentTitle = '';
        let isSeeking = false;

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
            currentTitle = '';

            if (playerTitle) playerTitle.textContent = 'Аудіо';
            if (seek) {
                seek.value = '0';
                seek.max = '0';
            }
            if (currentTimeEl) currentTimeEl.textContent = '0:00';
            if (durationEl) durationEl.textContent = '0:00';

            if (playerToggle) {
                playerToggle.textContent = '▶';
                playerToggle.setAttribute('aria-label', 'Відтворити');
            }

            if (player) player.classList.add('audio-player--hidden');
        }

        function formatTime(seconds) {
            const total = Math.max(0, Math.floor(Number(seconds) || 0));
            const m = Math.floor(total / 60);
            const s = total % 60;
            return `${m}:${String(s).padStart(2, '0')}`;
        }

        function showPlayer(title) {
            if (!player) return;
            player.classList.remove('audio-player--hidden');
            if (playerTitle) playerTitle.textContent = title || 'Аудіо';
        }

        function syncPlayerToggle() {
            if (!playerToggle) return;
            if (audio.paused) {
                playerToggle.textContent = '▶';
                playerToggle.setAttribute('aria-label', 'Відтворити');
            } else {
                playerToggle.textContent = '⏸';
                playerToggle.setAttribute('aria-label', 'Пауза');
            }
        }

        function syncPlayerTime() {
            if (!seek || !currentTimeEl || !durationEl) return;
            const duration = Number.isFinite(audio.duration) ? audio.duration : 0;
            const current = Number.isFinite(audio.currentTime) ? audio.currentTime : 0;

            durationEl.textContent = formatTime(duration);

            if (!isSeeking) {
                seek.max = String(duration || 0);
                seek.value = String(current || 0);
                currentTimeEl.textContent = formatTime(current);
            }
        }

        function syncCurrentCardPlayingState(isPlaying) {
            if (!currentStoryId) return;
            const card = document.querySelector(`.story-card[data-story-id="${currentStoryId}"]`);
            if (card) syncCardAudioButtons(card, isPlaying);
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
                    currentTitle = title;
                    currentAudioHref = normalizeUrl(audioUrl);
                    audio.src = currentAudioHref;
                    audio.play().catch(() => { /* ignore */ });

                    showPlayer(title);
                    syncPlayerToggle();

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
                        currentTitle = title;
                        currentAudioHref = requestedHref;
                        audio.src = currentAudioHref;
                        audio.play().catch(() => { /* ignore */ });
                        showPlayer(title);
                        syncPlayerToggle();
                        syncCardAudioButtons(card, true);
                        return;
                    }

                    if (audio.paused) {
                        audio.play().catch(() => { /* ignore */ });
                        syncCardAudioButtons(card, true);
                        syncPlayerToggle();
                    } else {
                        audio.pause();
                        syncCardAudioButtons(card, false);
                        syncPlayerToggle();
                    }
                }
            });
        });

        if (playerToggle) {
            playerToggle.addEventListener('click', () => {
                if (!currentAudioHref) return;
                if (audio.paused) {
                    audio.play().catch(() => { /* ignore */ });
                } else {
                    audio.pause();
                }
                syncPlayerToggle();
            });
        }

        if (seek) {
            const startSeeking = () => {
                isSeeking = true;
            };
            const stopSeeking = () => {
                isSeeking = false;
                syncPlayerTime();
            };

            seek.addEventListener('mousedown', startSeeking);
            seek.addEventListener('touchstart', startSeeking, { passive: true });
            window.addEventListener('mouseup', stopSeeking);
            window.addEventListener('touchend', stopSeeking);

            seek.addEventListener('input', () => {
                const value = Number(seek.value);
                if (currentTimeEl) currentTimeEl.textContent = formatTime(value);
                if (Number.isFinite(audio.duration) && audio.duration > 0) {
                    audio.currentTime = value;
                }
            });
        }

        audio.addEventListener('loadedmetadata', () => {
            showPlayer(currentTitle);
            syncPlayerTime();
            syncPlayerToggle();
        });

        audio.addEventListener('timeupdate', () => {
            syncPlayerTime();
        });

        audio.addEventListener('play', () => {
            syncPlayerToggle();
            syncCurrentCardPlayingState(true);
        });

        audio.addEventListener('pause', () => {
            syncPlayerToggle();
            if (audio.currentTime > 0) syncCurrentCardPlayingState(false);

            // reset when user manually stops
            if (audio.currentTime === 0) {
                currentStoryId = null;
                startedAt = 0;
            }
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

            stopAudio();
        });
    });
})();
