document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = Array.from(document.querySelectorAll('[data-tab-target]'));
    const tabPanels = Array.from(document.querySelectorAll('[data-tab-panel]'));

    if (!tabButtons.length || !tabPanels.length) {
        return;
    }

    const activatePanel = (panelId) => {
        tabButtons.forEach((button) => {
            const isActive = button.dataset.tabTarget === panelId;
            button.classList.toggle('is-active', isActive);
            button.setAttribute('aria-selected', isActive ? 'true' : 'false');
            button.setAttribute('tabindex', isActive ? '0' : '-1');
        });

        tabPanels.forEach((panel) => {
            panel.hidden = panel.id !== panelId;
        });
    };

    tabButtons.forEach((button) => {
        button.addEventListener('click', () => {
            activatePanel(button.dataset.tabTarget);
        });
    });

    const defaultTab = tabButtons.find((button) => button.dataset.default === 'true') || tabButtons[0];
    activatePanel(defaultTab.dataset.tabTarget);
});
