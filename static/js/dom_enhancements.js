(function () {
    function applyDataDrivenStyles() {
        document.querySelectorAll('[data-bg]').forEach(function (el) {
            var value = el.getAttribute('data-bg');
            if (value) el.style.background = value;
        });

        document.querySelectorAll('[data-bg-color]').forEach(function (el) {
            var value = el.getAttribute('data-bg-color');
            if (value) el.style.backgroundColor = value;
        });

        document.querySelectorAll('[data-bg-image]').forEach(function (el) {
            var url = el.getAttribute('data-bg-image');
            if (url) el.style.backgroundImage = "url('" + url.replace(/'/g, "%27") + "')";
        });

        document.querySelectorAll('[data-width]').forEach(function (el) {
            var raw = el.getAttribute('data-width');
            if (!raw) return;
            var num = parseFloat(raw);
            if (Number.isNaN(num)) return;
            var clamped = Math.max(0, Math.min(100, num));
            el.style.width = clamped + '%';
        });
    }

    function wireConfirmButtons() {
        document.querySelectorAll('[data-confirm]').forEach(function (btn) {
            if (btn.__confirmWired) return;
            btn.__confirmWired = true;

            btn.addEventListener('click', function (e) {
                var msg = btn.getAttribute('data-confirm') || 'Підтвердити дію?';
                if (!window.confirm(msg)) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            });
        });
    }

    function wireSidebarToggle() {
        document.querySelectorAll('[data-sidebar-toggle]').forEach(function (btn) {
            if (btn.__sidebarWired) return;
            btn.__sidebarWired = true;

            var sidebar = btn.closest('.sidebar');
            if (!sidebar) return;

            btn.addEventListener('click', function () {
                var isOpen = sidebar.classList.toggle('is-open');
                btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            });
        });
    }

    function init() {
        applyDataDrivenStyles();
        wireConfirmButtons();
        wireSidebarToggle();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
