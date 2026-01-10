from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.shortcuts import redirect, render

from students.models import StudentProfile
from students.forms import StudentProfileSpecialNeedsForm
from achievements.models import StudentAchievement
from progress.models import StudentProgress


@login_required
def profile(request):
	if not hasattr(request.user, 'student_profile'):
		# If the user is a child, ensure profile exists (older accounts may miss it)
		if getattr(request.user, 'role', None) == 'child':
			StudentProfile.objects.get_or_create(
				user=request.user,
				defaults={'special_needs': '', 'level': 1},
			)
		else:
			messages.error(request, 'Ця сторінка доступна тільки для дітей.')
			return redirect('/')

	profile = request.user.student_profile

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
		'chart_labels': chart_labels,
		'chart_scores': chart_scores,
	}
	return render(request, 'students/profile.html', context)


@login_required
def dashboard(request):
	return profile(request)
