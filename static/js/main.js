document.addEventListener('DOMContentLoaded', function () {
    console.log('IncludoLand loaded!');

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Don't auto-dismiss alerts that are hidden initially.
        // Some pages reveal alerts later (e.g., “Завершити” message in games).
        if (alert.classList.contains('d-none')) return;
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Optional voiceover for kid-friendly UI (click to speak)
    const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window;
    if (canSpeak) {
        document.body.addEventListener('click', (e) => {
            const el = e.target.closest('[data-speak]');
            if (!el) return;
            const text = (el.getAttribute('data-speak') || '').trim();
            if (!text) return;
            try {
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance(text);
                utter.lang = document.documentElement.lang || 'uk';
                window.speechSynthesis.speak(utter);
            } catch (_) {
                // no-op
            }
        });
    }
});
