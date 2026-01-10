from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TeacherProfile
from exercises.forms import ExerciseBlockForm, ExerciseTypeForm, QuestionForm

from students.models import StudentProfile

from .forms import TeacherProfileForm


@login_required
def dashboard(request):
    user = request.user
    if not hasattr(user, 'teacher_profile'):
        return render(request, 'teachers/not_teacher.html')

    profile = user.teacher_profile

    assigned_children = profile.students.select_related('user').all()

    context = {
        'profile': profile,
        'assigned_children': assigned_children,
    }
    return render(request, 'teachers/dashboard.html', context)


def _require_specialist(request):
    user = request.user
    if not user.is_authenticated:
        return None
    if hasattr(user, 'teacher_profile'):
        return user.teacher_profile
    return None


@login_required
def profile_edit(request):
    profile = _require_specialist(request)
    if not profile:
        return render(request, 'teachers/not_teacher.html')

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль оновлено.')
            return redirect('teachers:dashboard')
    else:
        form = TeacherProfileForm(instance=profile)

    return render(request, 'teachers/profile_edit.html', {'form': form})


@login_required
def add_child(request):
    profile = _require_specialist(request)
    if not profile:
        return render(request, 'teachers/not_teacher.html')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if not student_id:
            messages.error(request, 'Не вибрано дитину.')
            return redirect('teachers:add_child')
        student = get_object_or_404(StudentProfile, id=student_id)
        profile.students.add(student)
        messages.success(request, f"Дитину {student.user.username} додано до вашого списку.")
        return redirect('teachers:dashboard')

    q = (request.GET.get('q') or '').strip()
    students = StudentProfile.objects.select_related('user').all().order_by('user__username')
    if q:
        students = students.filter(user__username__icontains=q) | students.filter(user__email__icontains=q)
    return render(request, 'teachers/add_child.html', {'students': students[:200], 'q': q})


@login_required
def create_exercise_block(request):
    profile = _require_specialist(request)
    if not profile:
        return render(request, 'teachers/not_teacher.html')
    if request.method == 'POST':
        form = ExerciseBlockForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Навчальний блок створено!')
            return redirect('teachers:dashboard')
    else:
        form = ExerciseBlockForm()
    return render(request, 'exercises/block_form.html', {'form': form})


@login_required
def create_exercise_type(request):
    profile = _require_specialist(request)
    if not profile:
        return render(request, 'teachers/not_teacher.html')
    if request.method == 'POST':
        form = ExerciseTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тип вправи створено!')
            return redirect('teachers:dashboard')
    else:
        form = ExerciseTypeForm()
    return render(request, 'exercises/type_form.html', {'form': form})


@login_required
def create_question(request):
    profile = _require_specialist(request)
    if not profile:
        return render(request, 'teachers/not_teacher.html')

    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Питання створено!')
            return redirect('teachers:dashboard')
    else:
        form = QuestionForm()

    return render(request, 'exercises/question_form.html', {'form': form})
