document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('sound-form');
    const imageInput = document.getElementById('id_image');
    const titleInput = document.getElementById('id_title');
    const audioInput = document.getElementById('id_audio');

    const previewImg = document.getElementById('preview-img');
    const previewLabel = document.getElementById('preview-label');
    const previewPlay = document.getElementById('preview-play');
    const previewAudio = document.getElementById('preview-audio');

    const formTitle = document.getElementById('form-title');
    const saveBtn = document.getElementById('save-btn');
    const cancelBtn = document.getElementById('cancel-edit');
    const dropText = document.getElementById('drop-text');
    const audioBtnText = document.getElementById('audio-btn-text');
    const currentMedia = document.getElementById('current-media');
    const currentThumb = document.getElementById('current-thumb');
    const currentAudio = document.getElementById('current-audio');

    if (!form || !imageInput || !titleInput || !audioInput || !previewImg || !previewLabel || !previewPlay || !previewAudio) {
        return;
    }

    const createAction = form.dataset.createAction || form.getAttribute('action') || '';
    const editUrlTemplate = form.dataset.editUrlTemplate || '';

    let imageObjectUrl = null;
    let audioObjectUrl = null;
    let imageUrl = null; // current preview image url (object or existing)
    let audioUrl = null; // current preview audio url (object or existing)
    let editingCardId = null;

    function stopAllAudio() {
        try {
            previewAudio.pause();
            previewAudio.currentTime = 0;
        } catch (e) {
            // ignore
        }
        try {
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
            }
        } catch (e) {
            // ignore
        }
    }

    function buildEditUrl(cardId) {
        if (!editUrlTemplate) return '';
        return editUrlTemplate.replace('/0/', `/${cardId}/`);
    }

    function syncLabel() {
        const v = (titleInput.value || '').trim();
        previewLabel.textContent = v || '—';
    }

    function syncPlayState() {
        previewPlay.disabled = !(audioUrl);
    }

    titleInput.addEventListener('input', syncLabel);
    syncLabel();

    imageInput.addEventListener('change', () => {
        const file = imageInput.files && imageInput.files[0];
        if (!file) return;
        if (imageObjectUrl) URL.revokeObjectURL(imageObjectUrl);
        imageObjectUrl = URL.createObjectURL(file);
        imageUrl = imageObjectUrl;
        previewImg.style.backgroundImage = `url('${imageUrl}')`;
    });

    audioInput.addEventListener('change', () => {
        const file = audioInput.files && audioInput.files[0];
        if (!file) return;
        if (audioObjectUrl) URL.revokeObjectURL(audioObjectUrl);
        audioObjectUrl = URL.createObjectURL(file);
        audioUrl = audioObjectUrl;
        previewAudio.src = audioUrl;
        syncPlayState();
    });

    previewPlay.addEventListener('click', () => {
        if (!previewAudio.src) return;
        previewAudio.currentTime = 0;
        previewAudio.play().catch(() => {
            // ignore
        });
    });

    // Library cards playback
    const libButtons = Array.from(document.querySelectorAll('.lib-card__play'));
    let libAudio = null;

    libButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const url = btn.dataset.audioUrl;
            if (!url) return;
            if (!libAudio) libAudio = new Audio();
            libAudio.pause();
            libAudio.src = url;
            libAudio.currentTime = 0;
            libAudio.play().catch(() => {
                // ignore
            });
        });
    });

    const libCards = Array.from(document.querySelectorAll('.lib-card'));
    const editButtons = Array.from(document.querySelectorAll('.lib-card__edit'));

    function markSelected(cardId) {
        libCards.forEach(el => {
            const id = el.dataset.cardId;
            if (id && String(id) === String(cardId)) {
                el.classList.add('lib-card--selected');
            } else {
                el.classList.remove('lib-card--selected');
            }
        });
    }

    function setCreateMode() {
        editingCardId = null;
        markSelected(null);

        stopAllAudio();

        if (imageObjectUrl) {
            URL.revokeObjectURL(imageObjectUrl);
            imageObjectUrl = null;
        }
        if (audioObjectUrl) {
            URL.revokeObjectURL(audioObjectUrl);
            audioObjectUrl = null;
        }

        form.setAttribute('action', createAction);

        if (formTitle) formTitle.textContent = 'Додати новий звук';
        if (saveBtn) saveBtn.textContent = 'Зберегти картку';

        if (dropText) dropText.textContent = 'Завантажити зображення';
        if (audioBtnText) audioBtnText.textContent = 'Вибрати аудіофайл';

        imageInput.required = true;
        audioInput.required = true;

        titleInput.value = '';
        imageInput.value = '';
        audioInput.value = '';

        imageUrl = null;
        audioUrl = null;
        previewImg.style.backgroundImage = '';
        previewAudio.src = '';
        syncLabel();
        syncPlayState();

        if (currentMedia) currentMedia.classList.add('current--hidden');
        if (cancelBtn) cancelBtn.classList.add('cancel--hidden');
        if (currentThumb) currentThumb.style.backgroundImage = '';
        if (currentAudio) currentAudio.src = '';
    }

    function setEditModeFromCard(cardEl) {
        const cardId = cardEl.dataset.cardId;
        const cardTitle = cardEl.dataset.title || '';
        const cardImageUrl = cardEl.dataset.imageUrl || '';
        const cardAudioUrl = cardEl.dataset.audioUrl || '';

        if (!cardId) return;
        editingCardId = cardId;
        markSelected(cardId);

        stopAllAudio();

        // reset file inputs (cannot prefill, but clear any pending selection)
        imageInput.value = '';
        audioInput.value = '';

        // revoke previous object URLs if any
        if (imageObjectUrl) {
            URL.revokeObjectURL(imageObjectUrl);
            imageObjectUrl = null;
        }
        if (audioObjectUrl) {
            URL.revokeObjectURL(audioObjectUrl);
            audioObjectUrl = null;
        }

        const editUrl = buildEditUrl(cardId);
        if (editUrl) form.setAttribute('action', editUrl);

        if (formTitle) formTitle.textContent = 'Редагувати картку';
        if (saveBtn) saveBtn.textContent = 'Зберегти зміни';
        if (dropText) dropText.textContent = 'Замінити зображення (не обовʼязково)';
        if (audioBtnText) audioBtnText.textContent = 'Замінити аудіофайл (не обовʼязково)';

        imageInput.required = false;
        audioInput.required = false;

        titleInput.value = cardTitle;
        syncLabel();

        imageUrl = cardImageUrl;
        audioUrl = cardAudioUrl;

        previewImg.style.backgroundImage = cardImageUrl ? `url('${cardImageUrl}')` : '';
        previewAudio.src = cardAudioUrl || '';
        syncPlayState();

        if (currentMedia) currentMedia.classList.remove('current--hidden');
        if (cancelBtn) cancelBtn.classList.remove('cancel--hidden');
        if (currentThumb) currentThumb.style.backgroundImage = cardImageUrl ? `url('${cardImageUrl}')` : '';
        if (currentAudio) currentAudio.src = cardAudioUrl || '';
    }

    libCards.forEach(card => {
        card.addEventListener('click', () => setEditModeFromCard(card));
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setEditModeFromCard(card);
            }
        });
    });

    editButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const card = btn.closest('.lib-card');
            if (card) setEditModeFromCard(card);
        });
    });

    const deleteButtons = Array.from(document.querySelectorAll('.lib-card__delete button'));
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    });

    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => setCreateMode());
    }

    // default state: create mode (but allow server to request edit card selection)
    imageInput.required = true;
    audioInput.required = true;
    const requestedEditId = (form.dataset.editCardId || '').trim();
    if (requestedEditId) {
        const card = libCards.find(el => String(el.dataset.cardId) === String(requestedEditId));
        if (card) {
            setEditModeFromCard(card);
        }
    }
});
