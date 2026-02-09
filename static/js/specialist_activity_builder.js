const ready = (fn) => {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
};

const toggleHidden = (el, hide) => {
    if (!el) return;
    if (hide) {
        el.classList.add('is-hidden');
    } else {
        el.classList.remove('is-hidden');
    }
};

ready(() => {
    const previewTitle = document.getElementById('preview-title');
    const previewDescription = document.getElementById('preview-description');
    const previewTask = document.getElementById('preview-task');
    const previewImage = document.getElementById('preview-image');
    const previewImageEmpty = document.getElementById('preview-image-empty');
    const previewAudio = document.getElementById('preview-audio');
    const previewAudioEmpty = document.getElementById('preview-audio-empty');

    const updatePreview = (card) => {
        if (!card) return;
        const title = card.dataset.title || '';
        const description = card.dataset.description || '';
        const task = card.dataset.task || '';
        const image = card.dataset.image || '';
        const audio = card.dataset.audio || '';

        if (previewTitle) previewTitle.textContent = title;
        if (previewDescription) previewDescription.textContent = description;
        if (previewTask) previewTask.textContent = task;

        if (previewImage) {
            previewImage.src = image;
        }
        toggleHidden(previewImage, !image);
        toggleHidden(previewImageEmpty, !!image);

        if (previewAudio) {
            previewAudio.src = audio;
        }
        toggleHidden(previewAudio, !audio);
        toggleHidden(previewAudioEmpty, !!audio);

        document.querySelectorAll('.step-pill--active').forEach((el) => {
            el.classList.remove('step-pill--active');
        });
        card.classList.add('step-pill--active');
    };

    document.querySelectorAll('[data-step-pill]').forEach((btn) => {
        btn.addEventListener('click', (event) => {
            event.preventDefault();
            const card = btn.closest('.step-pill');
            updatePreview(card);
        });
    });

    const recordBtn = document.querySelector('[data-audio-record]');
    const audioInput = document.querySelector('[data-audio-input]');
    const recordStatus = document.getElementById('recording-status');
    let recorder = null;
    let chunks = [];
    let stream = null;

    const setStatus = (text) => {
        if (recordStatus) {
            recordStatus.textContent = text;
        }
    };

    const stopRecording = () => {
        if (!recorder) return;
        recorder.stop();
        recordBtn.textContent = 'Записати';
    };

    const startRecording = async () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setStatus('Запис не підтримується у вашому браузері.');
            return;
        }

        try {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            recorder = new MediaRecorder(stream);
            chunks = [];

            recorder.addEventListener('dataavailable', (event) => {
                if (event.data && event.data.size > 0) {
                    chunks.push(event.data);
                }
            });

            recorder.addEventListener('stop', () => {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                const file = new File([blob], 'recording.webm', { type: blob.type });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                if (audioInput) {
                    audioInput.files = dataTransfer.files;
                }
                if (stream) {
                    stream.getTracks().forEach((track) => track.stop());
                }
                setStatus('Запис додано. Ви можете завантажити інший файл за потреби.');
            });

            recorder.start();
            recordBtn.textContent = 'Зупинити';
            setStatus('Йде запис... Натисніть «Зупинити», щоб завершити.');
        } catch (error) {
            setStatus('Не вдалося отримати доступ до мікрофону.');
        }
    };

    if (recordBtn && audioInput) {
        recordBtn.addEventListener('click', () => {
            if (recorder && recorder.state === 'recording') {
                stopRecording();
            } else {
                startRecording();
            }
        });
    }
});
