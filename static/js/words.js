document.addEventListener('DOMContentLoaded', () => {
    const totalRoundsEl = document.getElementById('words-total');
    const roundEl = document.getElementById('words-round');
    const timeEl = document.getElementById('words-time');
    const hintEl = document.getElementById('words-hint');
    const emojiEl = document.getElementById('words-emoji');
    const slotsEl = document.getElementById('words-slots');
    const bankEl = document.getElementById('words-bank');
    const msgEl = document.getElementById('words-msg');
    const clearBtn = document.getElementById('words-clear');
    const startBtn = document.getElementById('words-start');
    const cardEl = document.querySelector('.words-card');

    if (!totalRoundsEl || !roundEl || !timeEl || !hintEl || !emojiEl || !slotsEl || !bankEl || !msgEl || !clearBtn || !startBtn || !cardEl) {
        return;
    }

    const WORDS = [
        { word: 'КІТ', hint: 'Домашній улюбленець, який муркоче', emoji: '🐱' },
        { word: 'ЛІС', hint: 'Багато дерев, можна почути пташок', emoji: '🌲' },
        { word: 'ДОЩ', hint: 'Капає з неба, потрібна парасоля', emoji: '🌧️' },
        { word: 'СОНЦЕ', hint: 'Світить вдень і гріє', emoji: '☀️' },
        { word: 'РИБА', hint: 'Плаває у воді', emoji: '🐟' },
        { word: 'КВІТКА', hint: 'Росте на клумбі і пахне', emoji: '🌸' },
        { word: 'МОРЕ', hint: 'Солона вода і хвилі', emoji: '🌊' },
        { word: 'ПТАХ', hint: 'Має крила і літає', emoji: '🐦' },
        { word: 'ВІТЕР', hint: 'Невидимий, але рухає листя', emoji: '💨' },
        { word: 'СНІГ', hint: 'Білий, падає взимку', emoji: '❄️' },
    ];

    const ALPHABET = 'АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ';

    const TOTAL_ROUNDS = 5;
    totalRoundsEl.textContent = String(TOTAL_ROUNDS);

    let round = 0;
    let correct = 0;
    let startTime = null;
    let timerId = null;

    let runWords = [];
    let current = null;
    let picked = [];

    function shuffle(arr) {
        const a = [...arr];
        for (let i = a.length - 1; i > 0; i -= 1) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function setState(state) {
        cardEl.dataset.state = state || '';
    }

    function updateTimer() {
        if (!startTime) {
            timeEl.textContent = '0';
            return;
        }
        const seconds = Math.floor((Date.now() - startTime) / 1000);
        timeEl.textContent = String(seconds);
    }

    function stopTimer() {
        if (timerId) window.clearInterval(timerId);
        timerId = null;
    }

    function startTimer() {
        stopTimer();
        timerId = window.setInterval(updateTimer, 250);
        updateTimer();
    }

    function renderSlots(wordLen) {
        slotsEl.innerHTML = '';
        for (let i = 0; i < wordLen; i += 1) {
            const slot = document.createElement('button');
            slot.type = 'button';
            slot.className = 'words-slot';
            slot.setAttribute('aria-label', 'Літера');
            slot.addEventListener('click', () => {
                // remove last letter on slot click
                removeLast();
            });
            slotsEl.appendChild(slot);
        }
    }

    function renderBank(letters) {
        bankEl.innerHTML = '';
        letters.forEach((ch) => {
            const tile = document.createElement('button');
            tile.type = 'button';
            tile.className = 'words-tile';
            tile.textContent = ch;
            tile.dataset.letter = ch;
            tile.addEventListener('click', () => {
                pickLetter(ch);
                tile.disabled = true;
                tile.style.opacity = '0.45';
            });
            bankEl.appendChild(tile);
        });
    }

    function fillSlotsFromPicked() {
        const slotButtons = Array.from(slotsEl.querySelectorAll('.words-slot'));
        slotButtons.forEach((slot, idx) => {
            const letter = picked[idx] || '';
            slot.textContent = letter;
            if (letter) slot.classList.add('words-slot--filled');
            else slot.classList.remove('words-slot--filled');
        });
    }

    function resetRoundUi() {
        picked = [];
        setState('');
        fillSlotsFromPicked();
        Array.from(bankEl.querySelectorAll('.words-tile')).forEach((t) => {
            t.disabled = false;
            t.style.opacity = '';
        });
        msgEl.textContent = 'Складай слово з літер.';
    }

    function removeLast() {
        if (!picked.length) return;
        const removed = picked.pop();
        fillSlotsFromPicked();
        setState('');

        // re-enable one matching tile (first disabled match)
        const tiles = Array.from(bankEl.querySelectorAll('.words-tile'));
        const tile = tiles.find(t => t.disabled && (t.dataset.letter === removed));
        if (tile) {
            tile.disabled = false;
            tile.style.opacity = '';
        }
    }

    function pickLetter(ch) {
        if (!current) return;
        if (picked.length >= current.word.length) return;
        picked.push(ch);
        fillSlotsFromPicked();
        setState('');

        if (picked.length === current.word.length) {
            checkAnswer();
        }
    }

    function makeLetterSet(word) {
        const base = [...word];
        const extraCount = Math.min(2, Math.max(0, 8 - base.length));
        const extra = [];
        while (extra.length < extraCount) {
            const ch = ALPHABET[Math.floor(Math.random() * ALPHABET.length)];
            if (!base.includes(ch) && !extra.includes(ch)) extra.push(ch);
        }
        return shuffle([...base, ...extra]);
    }

    function setRoundWord(item) {
        current = item;
        hintEl.textContent = item.hint;
        emojiEl.textContent = item.emoji;

        renderSlots(item.word.length);
        renderBank(makeLetterSet(item.word));
        resetRoundUi();
    }

    function nextRound() {
        if (round >= TOTAL_ROUNDS) {
            finish();
            return;
        }
        roundEl.textContent = String(round + 1);
        setState('');
        setRoundWord(runWords[round]);
    }

    function checkAnswer() {
        const guess = picked.join('');
        const target = current.word;
        const ok = guess === target;

        if (ok) {
            correct += 1;
            setState('correct');
            msgEl.textContent = 'Правильно!';
        } else {
            setState('wrong');
            msgEl.textContent = `Не зовсім. Правильне слово: ${target}`;
        }

        // lock tiles
        Array.from(bankEl.querySelectorAll('.words-tile')).forEach((t) => {
            t.disabled = true;
            t.style.opacity = '0.45';
        });

        window.setTimeout(() => {
            round += 1;
            nextRound();
        }, 1000);
    }

    function sendResult(scoreVal, durationMs) {
        const csrfToken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) return;

        fetch('/api/game-results/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                game_type: 'words',
                score: scoreVal,
                raw_score: correct,
                max_score: TOTAL_ROUNDS,
                duration_seconds: Math.round(durationMs / 1000),
            }),
        }).catch(() => {
            /* ignore network errors for now */
        });
    }

    function finish() {
        stopTimer();
        const duration = startTime ? Date.now() - startTime : 0;
        const percent = Math.round((correct / TOTAL_ROUNDS) * 100);
        sendResult(percent, duration);

        setState('');
        hintEl.textContent = 'Гру завершено. Натисни “Почати” щоб зіграти знову.';
        emojiEl.textContent = '✅';
        slotsEl.innerHTML = '';
        bankEl.innerHTML = '';
        msgEl.textContent = `Результат: ${correct}/${TOTAL_ROUNDS} (${percent}%)`;
        startBtn.textContent = 'Зіграти ще раз';
        startTime = null;
        timeEl.textContent = '0';
    }

    function start() {
        runWords = shuffle(WORDS).slice(0, TOTAL_ROUNDS);
        round = 0;
        correct = 0;
        startTime = Date.now();
        startTimer();
        startBtn.textContent = 'Перезапустити';
        msgEl.textContent = 'Складай слово з літер.';
        nextRound();
    }

    clearBtn.addEventListener('click', () => {
        if (!startTime) return;
        resetRoundUi();
    });

    startBtn.addEventListener('click', () => {
        start();
    });

    // Keyboard support: backspace removes last
    document.addEventListener('keydown', (e) => {
        if (!startTime) return;
        if (e.key === 'Backspace') {
            e.preventDefault();
            removeLast();
        }
    });
});
