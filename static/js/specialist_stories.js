document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('story-form');
    const titleInput = document.getElementById('id_title');
    const textArea = document.getElementById('id_text');
    const pdfInput = document.getElementById('id_pdf_file');
    const audioInput = document.getElementById('id_audio');

    const ctText = document.getElementById('ct_text');
    const ctPdf = document.getElementById('ct_pdf');
    const boxText = document.getElementById('box-text');
    const boxPdf = document.getElementById('box-pdf');

    const pdfDropText = document.getElementById('pdf-drop-text');
    const audioUploadText = document.getElementById('audio-upload-text');

    const formTitle = document.getElementById('form-title');
    const saveBtn = document.getElementById('save-btn');
    const cancelBtn = document.getElementById('cancel-edit');

    const currentMedia = document.getElementById('current-media');
    const currentPdf = document.getElementById('current-pdf');
    const currentAudio = document.getElementById('current-audio');

    const recordBtn = document.getElementById('record-btn');
    const recordTimeEl = document.getElementById('record-time');
    const audioPreview = document.getElementById('audio-preview');

    if (!form || !titleInput || !ctText || !ctPdf || !boxText || !boxPdf || !textArea || !pdfInput || !audioInput) return;

    const createAction = form.dataset.createAction || form.getAttribute('action') || '';
    const editUrlTemplate = form.dataset.editUrlTemplate || '';

    let editingStoryId = null;

    function buildEditUrl(storyId) {
        if (!editUrlTemplate) return '';
        return editUrlTemplate.replace('/0/', `/${storyId}/`);
    }

    function stopAllAudio() {
        try {
            if (audioPreview) {
                audioPreview.pause();
                audioPreview.currentTime = 0;
            }
        } catch { /* ignore */ }
        try {
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
            }
        } catch { /* ignore */ }
        try {
            if (listPlayer) {
                listPlayer.pause();
                listPlayer.currentTime = 0;
            }
        } catch { /* ignore */ }
    }

    function setContentType(type) {
        const isText = type === 'text';
        if (isText) {
            boxText.classList.remove('content-box--hidden');
            boxPdf.classList.add('content-box--hidden');
        } else {
            boxText.classList.add('content-box--hidden');
            boxPdf.classList.remove('content-box--hidden');
        }
    }

    function getSelectedContentType() {
        return ctPdf.checked ? 'pdf' : 'text';
    }

    ctText.addEventListener('change', () => setContentType('text'));
    ctPdf.addEventListener('change', () => setContentType('pdf'));
    setContentType(getSelectedContentType());

    pdfInput.addEventListener('change', () => {
        const file = pdfInput.files && pdfInput.files[0];
        if (!file) return;
        if (pdfDropText) pdfDropText.textContent = `PDF: ${file.name}`;
    });

    audioInput.addEventListener('change', () => {
        const file = audioInput.files && audioInput.files[0];
        if (!file) return;
        if (audioUploadText) audioUploadText.textContent = `Аудіо: ${file.name}`;
        if (audioPreview) {
            const url = URL.createObjectURL(file);
            audioPreview.src = url;
            audioPreview.classList.add('audio__preview--shown');
        }
    });

    // Inline edit from list
    const storyItems = Array.from(document.querySelectorAll('.story-item'));

    function markSelected(storyId) {
        storyItems.forEach(el => {
            if (String(el.dataset.storyId) === String(storyId)) el.classList.add('story-item--selected');
            else el.classList.remove('story-item--selected');
        });
    }

    function setCreateMode() {
        editingStoryId = null;
        markSelected(null);
        stopAllAudio();

        form.setAttribute('action', createAction);
        if (formTitle) formTitle.textContent = 'Додати нову казку';
        if (saveBtn) saveBtn.textContent = 'Зберегти казку';
        if (cancelBtn) cancelBtn.classList.add('cancel--hidden');

        titleInput.value = '';
        textArea.value = '';
        pdfInput.value = '';
        audioInput.value = '';

        if (pdfDropText) pdfDropText.textContent = 'Завантажити PDF';
        if (audioUploadText) audioUploadText.textContent = 'Завантажити аудіофайл';

        ctText.checked = true;
        ctPdf.checked = false;
        setContentType('text');

        if (audioPreview) {
            audioPreview.src = '';
            audioPreview.classList.remove('audio__preview--shown');
        }

        if (currentMedia) currentMedia.classList.add('current--hidden');
        if (currentPdf) currentPdf.setAttribute('href', '#');
        if (currentAudio) currentAudio.src = '';
    }

    function setEditModeFromItem(itemEl) {
        const storyId = itemEl.dataset.storyId;
        if (!storyId) return;

        editingStoryId = storyId;
        markSelected(storyId);
        stopAllAudio();

        const title = itemEl.dataset.title || '';
        const contentType = itemEl.dataset.contentType || 'text';
        let text = itemEl.dataset.text || '';
        // escapejs can leave sequences like \n, \r, \t in the attribute.
        text = text
            .replace(/\\r\\n/g, '\n')
            .replace(/\\n/g, '\n')
            .replace(/\\r/g, '\n')
            .replace(/\\t/g, '\t');
        const pdfUrl = itemEl.dataset.pdfUrl || '';
        const audioUrl = itemEl.dataset.audioUrl || '';

        const editUrl = buildEditUrl(storyId);
        if (editUrl) form.setAttribute('action', editUrl);

        if (formTitle) formTitle.textContent = 'Редагувати казку';
        if (saveBtn) saveBtn.textContent = 'Зберегти зміни';
        if (cancelBtn) cancelBtn.classList.remove('cancel--hidden');

        titleInput.value = title;
        textArea.value = text;

        // reset file inputs (cannot prefill)
        pdfInput.value = '';
        audioInput.value = '';
        if (pdfDropText) pdfDropText.textContent = 'Замінити PDF (не обовʼязково)';
        if (audioUploadText) audioUploadText.textContent = 'Замінити аудіо (не обовʼязково)';

        if (contentType === 'pdf') {
            ctPdf.checked = true;
            ctText.checked = false;
            setContentType('pdf');
        } else {
            ctText.checked = true;
            ctPdf.checked = false;
            setContentType('text');
        }

        if (currentMedia) currentMedia.classList.remove('current--hidden');
        if (currentPdf) {
            currentPdf.href = pdfUrl || '#';
            currentPdf.textContent = pdfUrl ? 'Відкрити' : 'Немає файлу';
            currentPdf.classList.toggle('current__link--disabled', !pdfUrl);
        }
        if (currentAudio) currentAudio.src = audioUrl || '';

        if (audioPreview) {
            audioPreview.src = '';
            audioPreview.classList.remove('audio__preview--shown');
        }
    }

    storyItems.forEach(item => {
        const editBtn = item.querySelector('.btn--edit');
        if (editBtn) {
            editBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                setEditModeFromItem(item);
            });
        }
        item.addEventListener('dblclick', () => setEditModeFromItem(item));
        item.addEventListener('click', (e) => {
            // clicking the audio icon shouldn't trigger edit
            const target = e.target;
            if (target && (target.classList?.contains('icon--audio') || target.closest?.('.icon--audio'))) return;
        });
    });

    if (cancelBtn) cancelBtn.addEventListener('click', () => setCreateMode());

    // Auto-enter edit mode after server-side validation errors
    const requestedEditId = (form.dataset.editStoryId || '').trim();
    if (requestedEditId) {
        const item = storyItems.find(el => String(el.dataset.storyId) === String(requestedEditId));
        if (item) setEditModeFromItem(item);
    }

    // Audio playback in list
    let listPlayer = null;
    const audioButtons = Array.from(document.querySelectorAll('.icon--audio'));
    audioButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const item = btn.closest('.story-item');
            const url = item?.dataset?.audioUrl;
            if (!url) return;
            if (!listPlayer) listPlayer = new Audio();
            listPlayer.pause();
            listPlayer.currentTime = 0;
            listPlayer.src = url;
            listPlayer.play().catch(() => { /* ignore */ });
        });
    });

    // Audio recording (MediaRecorder) -> attach to file input
    let recorder = null;
    let recording = false;
    let recordChunks = [];
    let recordTimer = null;
    let startedAt = 0;

    function fmtTime(ms) {
        const total = Math.floor(ms / 1000);
        const m = String(Math.floor(total / 60)).padStart(2, '0');
        const s = String(total % 60).padStart(2, '0');
        return `(${m}:${s})`;
    }

    async function startRecording() {
        if (!navigator.mediaDevices?.getUserMedia) {
            alert('Запис аудіо не підтримується у цьому браузері. Використайте завантаження аудіофайлу.');
            return;
        }
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '';
        recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
        recordChunks = [];

        recorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) recordChunks.push(e.data);
        };

        recorder.onstop = () => {
            try {
                stream.getTracks().forEach(t => t.stop());
            } catch { /* ignore */ }

            const blob = new Blob(recordChunks, { type: recorder.mimeType || 'audio/webm' });
            const fileExt = (blob.type || '').includes('webm') ? 'webm' : 'dat';
            const file = new File([blob], `story-audio.${fileExt}`, { type: blob.type || 'application/octet-stream' });

            // Put recorded file into the existing audio input
            try {
                const dt = new DataTransfer();
                dt.items.add(file);
                audioInput.files = dt.files;
                if (audioUploadText) audioUploadText.textContent = `Аудіо: ${file.name}`;
                if (audioPreview) {
                    const url = URL.createObjectURL(file);
                    audioPreview.src = url;
                    audioPreview.classList.add('audio__preview--shown');
                }
            } catch {
                alert('Не вдалося підставити запис у форму. Спробуйте завантажити файл вручну.');
            }
        };

        recorder.start();
        recording = true;
        startedAt = Date.now();
        if (recordBtn) recordBtn.textContent = '⏹ Зупинити запис';
        recordTimer = setInterval(() => {
            const ms = Date.now() - startedAt;
            if (recordTimeEl) recordTimeEl.textContent = fmtTime(ms);
        }, 250);
    }

    function stopRecording() {
        if (!recorder) return;
        try {
            recorder.stop();
        } catch { /* ignore */ }
        recording = false;
        if (recordTimer) clearInterval(recordTimer);
        recordTimer = null;
        if (recordTimeEl) recordTimeEl.textContent = '(00:00)';
        if (recordBtn) recordBtn.textContent = '🎙 Записати аудіо (00:00)';
    }

    if (recordBtn) {
        recordBtn.addEventListener('click', async () => {
            try {
                if (!recording) await startRecording();
                else stopRecording();
            } catch {
                alert('Не вдалося запустити запис. Перевірте доступ до мікрофону.');
                recording = false;
                stopRecording();
            }
        });
    }
});
