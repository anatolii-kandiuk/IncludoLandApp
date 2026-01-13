document.addEventListener('DOMContentLoaded', () => {
    const BG_URL = 'https://cdn.pixabay.com/photo/2017/02/20/18/03/children-2088770_1280.png';
    const spots = [
        { id: 'balloon', x: 78, y: 20 },
        { id: 'bench', x: 53, y: 54 },
        { id: 'dog', x: 48, y: 70 },
        { id: 'shoe', x: 63, y: 78 },
        { id: 'grass', x: 32, y: 60 },
    ];

    const leftCard = document.getElementById('left-card');
    const rightCard = document.getElementById('right-card');
    const hotspots = document.getElementById('hotspots');
    const overlay = document.getElementById('diff-overlay');
    const dotsEl = document.getElementById('dots');
    const progressText = document.getElementById('progress-text');
    const helperMsg = document.getElementById('helper-msg');

    if (!leftCard || !rightCard || !hotspots || !overlay || !dotsEl) return;

    leftCard.style.backgroundImage = `url(${BG_URL})`;
    rightCard.style.backgroundImage = `url(${BG_URL})`;

    const state = {
        found: new Set(),
        total: spots.length,
    };

    const updateProgress = () => {
        progressText.textContent = `${state.found.size}/${state.total}`;
        dotsEl.querySelectorAll('.dot').forEach((dot, idx) => {
            dot.classList.toggle('active', idx < state.found.size);
        });
    };

    const setMessage = (text) => {
        helperMsg.textContent = text;
    };

    const onFound = (id) => {
        state.found.add(id);
        updateProgress();
        if (state.found.size === state.total) {
            setMessage('Молодець! Усі відмінності знайдено.');
        } else {
            setMessage('Є ще відмінності, шукай далі!');
        }
    };

    const renderDots = () => {
        dotsEl.innerHTML = '';
        for (let i = 0; i < state.total; i += 1) {
            const dot = document.createElement('span');
            dot.className = 'dot';
            dotsEl.appendChild(dot);
        }
    };

    const renderSpots = () => {
        hotspots.innerHTML = '';
        overlay.innerHTML = '';
        spots.forEach((spot) => {
            const mark = document.createElement('span');
            mark.className = 'diff-mark';
            mark.style.left = `${spot.x}%`;
            mark.style.top = `${spot.y}%`;
            overlay.appendChild(mark);

            const btn = document.createElement('button');
            btn.className = 'hotspot';
            btn.type = 'button';
            btn.style.left = `${spot.x}%`;
            btn.style.top = `${spot.y}%`;
            btn.dataset.id = spot.id;
            btn.addEventListener('click', () => {
                if (state.found.has(spot.id)) return;
                state.found.add(spot.id);
                btn.classList.add('found');
                mark.style.opacity = '0';
                onFound(spot.id);
            });
            hotspots.appendChild(btn);
        });
    };

    renderDots();
    renderSpots();
    updateProgress();
    setMessage('Будь уважним! Натискай на відмінності праворуч.');
});
