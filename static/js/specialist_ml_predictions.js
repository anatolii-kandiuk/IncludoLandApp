document.addEventListener('DOMContentLoaded', () => {
	const form = document.getElementById('predictionForm');
	const loading = document.getElementById('loading');
	const result = document.getElementById('result');
	const gameTypesRaw = document.getElementById('mlGameTypes');

	if (!form || !loading || !result || !gameTypesRaw) {
		return;
	}

	const gameTypes = JSON.parse(gameTypesRaw.textContent || '[]')
		.reduce((acc, item) => {
			acc[item.value] = item.label;
			return acc;
		}, {});

	const formatDate = (value) => {
		if (!value) {
			return '-';
		}
		const date = new Date(value);
		if (Number.isNaN(date.getTime())) {
			return value;
		}
		return date.toLocaleString('uk-UA');
	};

	const toFixedOrDash = (value, digits = 1) => {
		if (value === null || value === undefined || Number.isNaN(Number(value))) {
			return '-';
		}
		return Number(value).toFixed(digits);
	};

	const toIntegerOrDash = (value) => {
		if (value === null || value === undefined || Number.isNaN(Number(value))) {
			return '-';
		}
		return `${Math.round(Number(value))}`;
	};

	const renderHistory = (history) => {
		if (!history.length) {
			return '<div class="ml-history-empty">Дані відсутні</div>';
		}

		const withScroll = history.length > 15;

		const rows = history.map((item) => `
			<div>${formatDate(item.created_at)}</div>
			<div>${toFixedOrDash(item.score, 1)}</div>
			<div>${toIntegerOrDash(item.duration_seconds)}</div>
			<div>${toIntegerOrDash(item.successful_attempts)}</div>
			<div>${toIntegerOrDash(item.failed_attempts)}</div>
		`).join('');

		return `
			<div class="ml-history-scroll ${withScroll ? 'is-scrollable' : ''}">
				<div class="ml-history-grid">
					<div class="ml-history-header">Дата</div>
					<div class="ml-history-header">Результат</div>
					<div class="ml-history-header">Тривалість (с)</div>
					<div class="ml-history-header">Вдалі спроби</div>
					<div class="ml-history-header">Невдалі спроби</div>
					${rows}
				</div>
			</div>
		`;
	};

	const renderMetrics = (modelInfo) => {
		const metrics = modelInfo.metrics || {};
		const modelState = modelInfo.analysis_mode === 'heuristic'
			? 'Накопичення даних'
			: (modelInfo.model_trained
				? 'Навчена зараз'
				: (modelInfo.model_loaded ? 'Завантажена' : 'Невідомо'));

		const metricLabelWithInfo = (label, hint) => `
			<span class="ml-stat-label-with-info">
				${label}
				<button
					type="button"
					class="ml-info-icon"
					aria-label="Пояснення: ${label}"
					data-tooltip="${hint}"
				>i</button>
			</span>
		`;

		return `
			<div class="ml-result-stats">
				<div class="ml-stat-card">
					<div class="ml-stat-label">Стан моделі</div>
					<div class="ml-stat-value">${modelState}</div>
				</div>
				<div class="ml-stat-card">
					<div class="ml-stat-label">${metricLabelWithInfo('Test MAE', 'Показує, наскільки в середньому прогноз моделі відрізняється від реального результату. Чим менше число — тим краще.')}</div>
					<div class="ml-stat-value">${toFixedOrDash(metrics.test_mae, 2)}</div>
				</div>
				<div class="ml-stat-card">
					<div class="ml-stat-label">${metricLabelWithInfo('Test RMSE', 'Також показує точність прогнозу, але сильніше реагує на великі промахи. Чим менше число — тим надійніший прогноз.')}</div>
					<div class="ml-stat-value">${toFixedOrDash(metrics.test_rmse, 2)}</div>
				</div>
			</div>
		`;
	};

	const renderMastery = (data, displayName) => {
		if (data.days_to_mastery) {
			return `
				<div class="ml-result-stats">
					<div class="ml-stat-card">
						<div class="ml-stat-label">Днів до майстерності (90+ балів)</div>
						<div class="ml-stat-value">${data.days_to_mastery}</div>
					</div>
					<div class="ml-stat-card">
						<div class="ml-stat-label">Спроб до майстерності</div>
						<div class="ml-stat-value">${data.attempts_to_mastery}</div>
					</div>
				</div>
			`;
		}

		const message = data.current_score >= 90
			? `${displayName} вже досяг(ла) майстерності! Чудовий результат!`
			: 'Продовжуйте практику для покращення результатів.';

		return `
			<div class="ml-mastery-box">
				<strong>Досягнення майстерності:</strong><br>
				${message}
			</div>
		`;
	};

	const displaySuccess = (data, username, gameType) => {
		const displayName = data.username || username;
		const modelInfo = data.model_info || {};
		const history = Array.isArray(data.history) ? data.history : [];
		const trendClass = data.score_trend > 0 ? 'ml-positive' : 'ml-negative';

		result.innerHTML = `
			<div class="prediction-result">
				<div class="result-title">
					Аналіз прогресу учня: <strong>${displayName}</strong>
				</div>
				<div class="ml-insight-box">
					<strong>Рекомендації для роботи з ${displayName}:</strong><br><br>
					<div class="ml-insight-content">${data.insight}</div>
				</div>
				<div class="ml-result-stats">
					<div class="ml-stat-card">
						<div class="ml-stat-label">Поточний результат</div>
						<div class="ml-stat-value">${toFixedOrDash(data.current_score, 1)}</div>
					</div>
					<div class="ml-stat-card">
						<div class="ml-stat-label">Прогноз наступного результату</div>
						<div class="ml-stat-value ml-stat-value-big">${toFixedOrDash(data.predicted_score, 1)}</div>
					</div>
					<div class="ml-stat-card">
						<div class="ml-stat-label">Тренд (+/- за активність)</div>
						<div class="ml-stat-value ${trendClass}">
							${data.score_trend > 0 ? '+' : ''}${toFixedOrDash(data.score_trend, 2)}
						</div>
					</div>
					<div class="ml-stat-card">
						<div class="ml-stat-label">Впевненість аналізу</div>
						<div class="ml-stat-value">${toFixedOrDash(data.confidence, 0)}%</div>
					</div>
				</div>
				${renderMetrics(modelInfo)}
				${renderMastery(data, displayName)}
				<div class="ml-history-box">
					<strong>Історія результатів активності:</strong>
					${renderHistory(history)}
				</div>
				<div class="ml-meta-box">
					<strong>Тип активності:</strong> ${gameTypes[gameType] || gameType}<br>
					<strong>Учень:</strong> ${displayName} (${username})
				</div>
			</div>
		`;

		result.classList.remove('ml-hidden');
	};

	const displayError = (data) => {
		const modelInfo = data.model_info || {};
		const history = Array.isArray(data.history) ? data.history : [];

		result.innerHTML = `
			<div class="prediction-result error">
				<div class="result-title">Не вдалося отримати прогноз</div>
				<div class="ml-error-box">
					<p class="error-message">${data.error || 'Невідома помилка'}</p>
					${data.reason ? `<p><strong>Причина:</strong> ${data.reason}</p>` : ''}
					${data.suggestion ? `<p><strong>Рекомендація:</strong> ${data.suggestion}</p>` : ''}
					${data.details ? `<p><strong>Деталі відповіді:</strong> ${data.details.substring(0, 300)}</p>` : ''}
				</div>
				${renderMetrics(modelInfo)}
				<div class="ml-history-box">
					<strong>Історія результатів активності:</strong>
					${renderHistory(history)}
				</div>
			</div>
		`;

		result.classList.remove('ml-hidden');
	};

	form.addEventListener('submit', async (event) => {
		event.preventDefault();

		const username = document.getElementById('studentSelect').value;
		const gameType = document.getElementById('gameTypeSelect').value;

		if (!username || !gameType) {
			alert('Будь ласка, оберіть учня та тип активності');
			return;
		}

		loading.classList.add('active');
		result.classList.add('ml-hidden');

		try {
			const apiUrl = form.dataset.apiUrl;
			const requestUrl = `${apiUrl}?username=${encodeURIComponent(username)}&game_type=${encodeURIComponent(gameType)}`;
			const response = await fetch(requestUrl, {
				method: 'GET',
				headers: {
					'X-Requested-With': 'XMLHttpRequest',
					'Accept': 'application/json'
				}
			});

			loading.classList.remove('active');

			const contentType = response.headers.get('content-type') || '';

			if (!response.ok) {
				if (contentType.includes('application/json')) {
					const errorData = await response.json();
					displayError(errorData);
				} else {
					const text = await response.text();
					displayError({
						error: 'Помилка сервера',
						reason: `HTTP ${response.status}: ${response.statusText}`,
						suggestion: 'Перевірте чи запущений сервер та база даних',
						details: text
					});
				}
				return;
			}

			if (!contentType.includes('application/json')) {
				const text = await response.text();
				displayError({
					error: 'Отримано неочікувану відповідь сервера',
					reason: 'Сервер повернув не JSON',
					suggestion: 'Перевірте чи ви увійшли в систему та чи доступний API',
					details: text
				});
				return;
			}

			const data = await response.json();
			displaySuccess(data, username, gameType);
		} catch (error) {
			loading.classList.remove('active');
			console.error('Fetch error:', error);
			displayError({
				error: 'Помилка підключення до сервера',
				reason: error.message,
				suggestion: 'Перевірте чи запущений Django сервер (python manage.py runserver)'
			});
		}
	});
});
