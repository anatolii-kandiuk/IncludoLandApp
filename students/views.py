from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from students.models import StudentGameResult, StudentProfile
from students.forms import StudentProfileSpecialNeedsForm
from achievements.models import StudentAchievement
from progress.models import StudentProgress


def _require_student_profile(request):
	if not request.user.is_authenticated:
		return None
	if hasattr(request.user, 'student_profile'):
		return request.user.student_profile
	# If the user is a child, ensure profile exists (older accounts may miss it)
	if getattr(request.user, 'role', None) == 'child':
		profile, _ = StudentProfile.objects.get_or_create(
			user=request.user,
			defaults={'special_needs': '', 'level': 1},
		)
		return profile
	return None


@login_required
def profile(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')

	if request.method == 'POST':
		form = StudentProfileSpecialNeedsForm(request.POST, instance=profile)
		if form.is_valid():
			form.save()
			messages.success(request, 'Опис особливостей збережено.')
			return redirect('students:profile')
	else:
		form = StudentProfileSpecialNeedsForm(instance=profile)
	progress_qs = StudentProgress.objects.filter(student=profile)

	agg = progress_qs.aggregate(
		avg_score=Avg('score'),
		sum_correct=Sum('correct'),
		sum_total=Sum('total_questions'),
		sessions=Sum('attempts'),
	)
	completed_count = progress_qs.filter(completed=True).count()
	sum_correct = int(agg.get('sum_correct') or 0)
	sum_total = int(agg.get('sum_total') or 0)
	accuracy = int(round((sum_correct / sum_total * 100))) if sum_total > 0 else 0
	avg_score = float(agg.get('avg_score') or 0.0)

	recent_progress = list(
		progress_qs.select_related('exercise_type', 'exercise').order_by('-created_at')[:8]
	)

	chart_points = list(
		progress_qs.filter(completed=True)
		.select_related('exercise_type')
		.order_by('-created_at')[:14]
	)
	chart_points.reverse()
	chart_labels = [p.created_at.strftime('%d.%m') for p in chart_points]
	chart_scores = [float(p.score or 0.0) for p in chart_points]

	achievements = list(
		StudentAchievement.objects.filter(student=profile)
		.select_related('achievement')
		.order_by('-awarded_at')
	)

	# Games stats: latest result per game
	latest_by_key = {}
	for r in StudentGameResult.objects.filter(student=profile).order_by('-played_at', '-id'):
		if r.game_key not in latest_by_key:
			latest_by_key[r.game_key] = r
		if len(latest_by_key) >= 12:
			break
	game_results = list(latest_by_key.values())
	game_results.sort(key=lambda x: x.game_name)
	game_chart_labels = [r.game_name for r in game_results]
	game_chart_scores = [int(r.score or 0) for r in game_results]

	context = {
		'profile': profile,
		'special_needs_form': form,
		'stats': {
			'completed_count': completed_count,
			'total_questions': sum_total,
			'accuracy': accuracy,
			'avg_score': int(round(avg_score)),
		},
		'recent_progress': recent_progress,
		'achievements': achievements,
		'game_results': game_results,
		'chart_labels': game_chart_labels,
		'chart_scores': game_chart_scores,
	}
	return render(request, 'students/profile.html', context)


@require_POST
@login_required
def game_finish(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')

	allowed = {
		'memory': 'Пам’ять',
		'attention': 'Увага',
		'speech': 'Мовлення',
		'math': 'Математика',
	}
	game_key = (request.POST.get('game') or '').strip()
	game_name = allowed.get(game_key)
	if not game_name:
		messages.error(request, 'Невідома гра.')
		return redirect('students:games')

	score_raw = (request.POST.get('score') or '').strip()
	try:
		score = int(float(score_raw)) if score_raw != '' else 0
	except (TypeError, ValueError):
		score = 0
	score = max(0, min(100, score))

	StudentGameResult.objects.create(
		student=profile,
		game_key=game_key,
		game_name=game_name,
		score=score,
	)
	messages.success(request, 'Ти молодець, продовжуй в тому ж дусі.')
	return redirect('students:games')


@login_required
def dashboard(request):
	return profile(request)


@login_required
def games(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')
	return render(request, 'students/games/index.html', {'profile': profile})


@login_required
def game_memory(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')
	return render(request, 'students/games/memory.html', {'profile': profile})


@login_required
def game_attention(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')
	return render(request, 'students/games/attention.html', {'profile': profile})


@login_required
def game_speech(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')
	return render(request, 'students/games/speech.html', {'profile': profile})


@login_required
def game_math(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')
	return render(request, 'students/games/math.html', {'profile': profile})


@login_required
def rewards(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')

	from achievements.models import Reward, RewardRedemption

	if request.method == 'POST':
		reward_id = request.POST.get('reward_id')
		reward = Reward.objects.filter(id=reward_id).first()
		if not reward:
			messages.error(request, 'Нагороду не знайдено.')
			return redirect('students:rewards')
		if profile.stars < reward.cost:
			messages.error(request, 'Недостатньо зірочок для цієї нагороди.')
			return redirect('students:rewards')
		# Redeem
		RewardRedemption.objects.create(student=profile, reward=reward, cost=reward.cost)
		profile.stars = max(0, profile.stars - reward.cost)
		profile.save(update_fields=['stars', 'updated_at'])
		messages.success(request, f'Вітаємо! Ви отримали нагороду: {reward.name}')
		return redirect('students:rewards')

	rewards_list = list(Reward.objects.all().order_by('cost', 'name'))
	redeemed = list(
		RewardRedemption.objects.filter(student=profile)
		.select_related('reward')
		.order_by('-redeemed_at')[:20]
	)
	return render(
		request,
		'students/rewards.html',
		{
			'profile': profile,
			'rewards': rewards_list,
			'redeemed': redeemed,
		},
	)


@login_required
def audiostories(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')

	from .models import AudioStory
	items = list(AudioStory.objects.filter(is_active=True).order_by('title'))
	return render(request, 'students/audiostories.html', {'profile': profile, 'items': items})


@login_required
def nature_sounds(request):
	profile = _require_student_profile(request)
	if not profile:
		messages.error(request, 'Ця сторінка доступна тільки для дітей.')
		return redirect('/')

	from .models import NatureSound
	items = list(NatureSound.objects.filter(is_active=True).order_by('category', 'title'))
	return render(request, 'students/nature_sounds.html', {'profile': profile, 'items': items})
