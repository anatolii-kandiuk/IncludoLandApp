(() => {
    function parseJSON(attr) {
        try {
            return JSON.parse(attr || '[]');
        } catch (_e) {
            return [];
        }
    }

    function initActivity() {
        const el = document.getElementById('activityChart');
        if (!el || !window.Chart) return;

        const labels = parseJSON(el.getAttribute('data-labels'));
        const yellow = parseJSON(el.getAttribute('data-yellow'));
        const teal = parseJSON(el.getAttribute('data-teal'));

        // eslint-disable-next-line no-new
        new window.Chart(el.getContext('2d'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Памʼять',
                        data: yellow,
                        borderColor: '#f7c948',
                        backgroundColor: 'rgba(247,201,72,.18)',
                        tension: 0.35,
                        pointRadius: 2,
                    },
                    {
                        label: 'Логіка',
                        data: teal,
                        borderColor: '#20b7b1',
                        backgroundColor: 'rgba(32,183,177,.12)',
                        tension: 0.35,
                        pointRadius: 2,
                    },
                ],
            },
            options: {
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: true },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0,0,0,.06)' },
                    },
                    x: {
                        grid: { display: false },
                    },
                },
            },
        });
    }

    function initPerformance() {
        const el = document.getElementById('performanceChart');
        if (!el || !window.Chart) return;

        const labels = parseJSON(el.getAttribute('data-labels'));
        const datasetsRaw = parseJSON(el.getAttribute('data-datasets'));

        const datasets = Array.isArray(datasetsRaw)
            ? datasetsRaw.map((d) => ({
                label: d.label || '',
                data: Array.isArray(d.data) ? d.data : [],
                borderColor: d.color || '#2b97e5',
                backgroundColor: 'rgba(43,151,229,.08)',
                tension: 0.35,
                pointRadius: 2,
                spanGaps: true,
            }))
            : [];

        // eslint-disable-next-line no-new
        new window.Chart(el.getContext('2d'), {
            type: 'line',
            data: { labels, datasets },
            options: {
                plugins: {
                    legend: { display: datasets.length > 1 },
                    tooltip: { enabled: true },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        suggestedMax: 100,
                        ticks: { callback: (v) => `${v}%` },
                        grid: { color: 'rgba(0,0,0,.06)' },
                    },
                    x: {
                        grid: { display: false },
                    },
                },
            },
        });
    }

    window.addEventListener('DOMContentLoaded', () => {
        initActivity();
        initPerformance();
    });
})();
