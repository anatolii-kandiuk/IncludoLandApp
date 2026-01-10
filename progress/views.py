from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Max, Count
import csv
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from .models import StudentProgress


@login_required
def dashboard(request):
    # Only for students
    if hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
        progress_list = StudentProgress.objects.filter(student=student, exercise_type__isnull=False).order_by('-updated_at')
    else:
        progress_list = []
    return render(request, 'progress/dashboard.html', {'progress_list': progress_list})

@staff_member_required
def admin_stats(request):
    # students = StudentProfile.objects.select_related('user').all()  # students app видалено
    students = []
    progress = StudentProgress.objects.select_related('student', 'exercise_type').all()
    # Фільтри
    exercise_type_filter = request.GET.get('exercise_type')
    student_filter = request.GET.get('student')
    if exercise_type_filter:
        progress = progress.filter(exercise_type__name=exercise_type_filter)
    if student_filter:
        progress = progress.filter(student__user__username=student_filter)
    # Aggregate stats by student and exercise_type
    summary = {}
    for p in progress:
        key = (p.student.user.username, p.exercise_type.name)
        if key not in summary:
            summary[key] = {
                'attempts': 0,
                'correct': 0,
                'total': 0,
                'max_score': 0,
                'last_score': 0,
                'count': 0,
            }
        summary[key]['attempts'] += p.attempts
        summary[key]['correct'] += p.correct
        summary[key]['total'] += p.total_questions
        summary[key]['max_score'] = max(summary[key]['max_score'], p.score)
        summary[key]['last_score'] = p.score
        summary[key]['count'] += 1
    # For filter UI
    exercise_types = set(p.exercise_type.name for p in StudentProgress.objects.select_related('exercise_type'))
    student_usernames = set(s.user.username for s in students)
    return render(request, 'progress/admin_stats.html', {
        'students': students,
        'summary': summary,
        'exercise_types': sorted(exercise_types),
        'student_usernames': sorted(student_usernames),
    })

@staff_member_required
def export_stats_csv(request):
    progress = StudentProgress.objects.select_related('student', 'exercise_type').all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_stats.csv"'
    writer = csv.writer(response)
    writer.writerow(['Учень', 'Тип вправи', 'Спроб', 'Правильних', 'Всього питань', 'Найкращий результат', 'Останній результат', 'Всього проходжень'])
    summary = {}
    for p in progress:
        key = (p.student.user.username, p.exercise_type.name)
        if key not in summary:
            summary[key] = {
                'attempts': 0,
                'correct': 0,
                'total': 0,
                'max_score': 0,
                'last_score': 0,
                'count': 0,
            }
        summary[key]['attempts'] += p.attempts
        summary[key]['correct'] += p.correct
        summary[key]['total'] += p.total_questions
        summary[key]['max_score'] = max(summary[key]['max_score'], p.score)
        summary[key]['last_score'] = p.score
        summary[key]['count'] += 1
    for key, stat in summary.items():
        writer.writerow([
            key[0], key[1], stat['attempts'], stat['correct'], stat['total'],
            f"{stat['max_score']:.0f}%", f"{stat['last_score']:.0f}%", stat['count']
        ])
    return response

@staff_member_required
def export_stats_pdf(request):
    progress = StudentProgress.objects.select_related('student', 'exercise_type').all()
    # Фільтри як у CSV
    exercise_type_filter = request.GET.get('exercise_type')
    student_filter = request.GET.get('student')
    if exercise_type_filter:
        progress = progress.filter(exercise_type__name=exercise_type_filter)
    if student_filter:
        progress = progress.filter(student__user__username=student_filter)
    summary = {}
    for p in progress:
        key = (p.student.user.username, p.exercise_type.name)
        if key not in summary:
            summary[key] = {
                'attempts': 0,
                'correct': 0,
                'total': 0,
                'max_score': 0,
                'last_score': 0,
                'count': 0,
            }
        summary[key]['attempts'] += p.attempts
        summary[key]['correct'] += p.correct
        summary[key]['total'] += p.total_questions
        summary[key]['max_score'] = max(summary[key]['max_score'], p.score)
        summary[key]['last_score'] = p.score
        summary[key]['count'] += 1
    template = get_template('progress/admin_stats_pdf.html')
    html = template.render({'summary': summary, 'request': request})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="student_stats.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

@staff_member_required
def student_detail(request, username):
    # student = StudentProfile.objects.select_related('user').get(user__username=username)  # students app видалено
    student = None
    progress_list = StudentProgress.objects.filter(student=student, exercise_type__isnull=False).order_by('-updated_at')
    return render(request, 'progress/student_detail.html', {'student': student, 'progress_list': progress_list})
