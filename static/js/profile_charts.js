(() => {
    function parseData(el) {
        const labelsRaw = el.getAttribute('data-labels');
        const valuesRaw = el.getAttribute('data-values');
        let labels = [];
        let values = [];
        try {
            labels = JSON.parse(labelsRaw || '[]');
            values = JSON.parse(valuesRaw || '[]');
        } catch (_e) {
            labels = [];
            values = [];
        }
        return { labels, values };
    }

    function initLine() {
        const el = document.getElementById('lineChart');
        if (!el || !window.Chart) return;
        const { labels, values } = parseData(el);

        // eslint-disable-next-line no-new
        new window.Chart(el.getContext('2d'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Успішність',
                        data: values,
                        borderColor: '#2b97e5',
                        backgroundColor: 'rgba(43,151,229,.15)',
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3,
                        pointHoverRadius: 4,
                    },
                ],
            },
            options: {
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    y: {
                        beginAtZero: true,
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

    function initRadar() {
        const el = document.getElementById('radarChart');
        if (!el || !window.Chart) return;
        const { labels, values } = parseData(el);

        // eslint-disable-next-line no-new
        new window.Chart(el.getContext('2d'), {
            type: 'radar',
            data: {
                labels,
                datasets: [
                    {
                        data: values,
                        borderColor: '#2b97e5',
                        backgroundColor: 'rgba(43,151,229,.18)',
                        pointRadius: 2,
                    },
                ],
            },
            options: {
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        suggestedMax: 100,
                        grid: { color: 'rgba(0,0,0,.06)' },
                        angleLines: { color: 'rgba(0,0,0,.06)' },
                        pointLabels: { color: '#152a28', font: { weight: '700' } },
                        ticks: { display: false },
                    },
                },
            },
        });
    }

    window.addEventListener('DOMContentLoaded', () => {
        initLine();
        initRadar();
    });
})();
