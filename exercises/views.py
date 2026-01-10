from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import Exercise, ExerciseCategory, ExerciseBlock, ExerciseType, Question
import random
import re


TASKS_LIMIT_DEFAULT = 10


def _ensure_question_options(question, count=3):
    """Ensure a question has a multiple-choice options list."""
    if question.options and len(question.options) > 0:
        return

    ca = (question.correct_answer or '').strip()

    def _generate_numeric_options(correct_str, count=3):
        try:
            base = int(correct_str)
        except Exception:
            return [correct_str]
        opts = set([base])
        delta = 1
        while len(opts) < count:
            opts.add(base + delta)
            if len(opts) < count:
                opts.add(base - delta)
            delta += 1
        opts_list = [str(x) for x in opts]
        random.shuffle(opts_list)
        return opts_list[:count]

    def _generate_letter_options(correct_letter, count=3):
        uk_letters = ['А','Б','В','Г','Ґ','Д','Е','Є','Ж','З','И','І','Ї','Й','К','Л','М','Н','О','П','Р','С','Т','У','Ф','Х','Ц','Ч','Ш','Щ','Ь','Ю','Я']
        correct = correct_letter.upper()
        candidates = [l for l in uk_letters if l != correct]
        random.shuffle(candidates)
        opts = [correct] + candidates[:count-1]
        random.shuffle(opts)
        return opts

    if re.fullmatch(r"-?\d+", ca):
        question.options = _generate_numeric_options(ca, count=count)
    elif re.fullmatch(r"[А-ЯІЇЄҐа-яіїєґ]", ca):
        question.options = _generate_letter_options(ca, count=count)
    else:
        base = ca or 'варіант'
        opts = [base]
        suffixes = [' (a)', ' (b)', ' (c)']
        i = 0
        while len(opts) < count:
            opts.append(f"{base}{suffixes[i]}")
            i += 1
        random.shuffle(opts)
        question.options = opts


def _select_questions_variant(exercise_type, limit, variant_n=None, start_question_id=None):
    base_questions = list(Question.objects.filter(exercise_type=exercise_type).order_by('order', 'id'))
    if not base_questions:
        return []

    start_index = 0
    if variant_n is not None:
        start_index = (variant_n - 1) % len(base_questions)
    elif start_question_id is not None:
        for idx, q in enumerate(base_questions):
            if q.id == start_question_id:
                start_index = idx
                break

    # Always return `limit` items; repeat only if there are fewer base questions.
    return [base_questions[(start_index + i) % len(base_questions)] for i in range(limit)]


def block_list(request):
    """Show all learning blocks (Math, Language, etc.)"""
    # Some DB states may contain duplicated blocks (e.g. same name created twice).
    # For the child UI we show each block name only once.
    blocks_qs = ExerciseBlock.objects.all().order_by('order', 'name', 'id')
    seen_names = set()
    blocks = []
    for b in blocks_qs:
        key = (b.name or '').strip().lower()
        if not key or key in seen_names:
            continue
        seen_names.add(key)
        blocks.append(b)

    context = {'blocks': blocks}
    return render(request, 'exercises/block_list.html', context)


def exercise_type_list(request, block_slug):
    """Show exercise types within a block"""
    block = get_object_or_404(ExerciseBlock, slug=block_slug)
    exercise_types = ExerciseType.objects.filter(block=block, is_active=True)
    
    context = {
        'block': block,
        'exercise_types': exercise_types,
    }
    return render(request, 'exercises/type_list.html', context)


def quiz_view(request, block_slug, type_slug):
    """Show quiz with multiple questions"""
    exercise_block = get_object_or_404(ExerciseBlock, slug=block_slug)
    exercise_type = get_object_or_404(ExerciseType, block=exercise_block, slug=type_slug, is_active=True)

    questions_qs = Question.objects.filter(exercise_type=exercise_type)
    questions = list(questions_qs)

    for q in questions:
        _ensure_question_options(q, count=3)
    
    if not questions:
        messages.warning(request, 'Немає питань для цієї вправи')
        return redirect('exercises:type_list', block_slug=block_slug)

    context = {
        'block': exercise_block,
        'exercise_type': exercise_type,
        'questions': questions,
    }
    return render(request, 'exercises/quiz.html', context)


def task_list(request, block_slug, type_slug):
    """List tasks within an exercise type (each question is a task)."""
    tasks_limit = TASKS_LIMIT_DEFAULT
    block = get_object_or_404(ExerciseBlock, slug=block_slug)
    exercise_type = get_object_or_404(ExerciseType, block=block, slug=type_slug, is_active=True)
    base_tasks = list(
        Question.objects.filter(exercise_type=exercise_type)
        .order_by('order', 'id')
    )

    if not base_tasks:
        tasks = []
    elif len(base_tasks) >= tasks_limit:
        tasks = base_tasks[:tasks_limit]
    else:
        # Repeat teacher-created examples to reach a minimum of 10.
        extended = []
        while len(extended) < tasks_limit:
            extended.extend(base_tasks)
        tasks = extended[:tasks_limit]

    context = {
        'block': block,
        'exercise_type': exercise_type,
        'tasks': tasks,
        'tasks_limit': tasks_limit,
    }
    return render(request, 'exercises/task_list.html', context)


def task_view(request, block_slug, type_slug, question_id):
    """Solve a single task (worksheet variant with multiple examples)."""
    tasks_limit = TASKS_LIMIT_DEFAULT
    block = get_object_or_404(ExerciseBlock, slug=block_slug)
    exercise_type = get_object_or_404(ExerciseType, block=block, slug=type_slug, is_active=True)
    # Task number (variant) provided from the list (e.g. ?n=3)
    task_number = None
    try:
        n = int(request.GET.get('n', '') or 0)
        if 1 <= n <= tasks_limit:
            task_number = n
    except Exception:
        task_number = None

    # Validate that question_id belongs to the type (keeps URL stable), but selection is variant-based.
    get_object_or_404(Question, pk=question_id, exercise_type=exercise_type)
    variant_n = task_number or 1
    questions = _select_questions_variant(exercise_type, tasks_limit, variant_n=variant_n)
    for q in questions:
        _ensure_question_options(q, count=3)

    context = {
        'block': block,
        'exercise_type': exercise_type,
        'questions': questions,
        'tasks_mode': True,
        'task_number': variant_n,
        'tasks_url': reverse('exercises:task_list', kwargs={'block_slug': block_slug, 'type_slug': type_slug}),
        'submit_url': reverse('exercises:task_submit', kwargs={'block_slug': block_slug, 'type_slug': type_slug, 'question_id': question_id}) + f'?n={variant_n}',
        'print_url': reverse('exercises:quiz_print', kwargs={'block_slug': block_slug, 'type_slug': type_slug}) + f'?n={variant_n}',
    }
    return render(request, 'exercises/quiz.html', context)


def task_submit(request, block_slug, type_slug, question_id):
    if request.method != 'POST':
        return redirect('exercises:task_view', block_slug=block_slug, type_slug=type_slug, question_id=question_id)

    block = get_object_or_404(ExerciseBlock, slug=block_slug)
    exercise_type = get_object_or_404(ExerciseType, block=block, slug=type_slug, is_active=True)

    tasks_limit = TASKS_LIMIT_DEFAULT
    get_object_or_404(Question, pk=question_id, exercise_type=exercise_type)
    try:
        variant_n = int(request.GET.get('n', '') or 1)
    except Exception:
        variant_n = 1
    if variant_n < 1:
        variant_n = 1

    questions = _select_questions_variant(exercise_type, tasks_limit, variant_n=variant_n)
    correct_count = 0
    total_questions = len(questions)
    for q in questions:
        user_answer = request.POST.get(f'answer_{q.id}', '').strip()
        if user_answer.lower() == (q.correct_answer or '').strip().lower():
            correct_count += 1
    score = int(round((correct_count / total_questions * 100))) if total_questions > 0 else 0

    if getattr(request, 'user', None) and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile


        # Save a progress entry (used by the student dashboard chart)
        try:
            from progress.models import StudentProgress

            StudentProgress.objects.create(
                student=profile,
                exercise_type=exercise_type,
                attempts=1,
                correct=correct_count,
                total_questions=total_questions,
                time_spent=0,
                score=score,
                completed=True,
            )

            # Minimal achievements (optional, but makes the dashboard meaningful)
            try:
                from achievements.models import Achievement, StudentAchievement

                def _award(code: str, title: str, description: str):
                    ach, _ = Achievement.objects.get_or_create(
                        code=code,
                        defaults={'title': title, 'description': description},
                    )
                    StudentAchievement.objects.get_or_create(student=profile, achievement=ach)

                completed_count = StudentProgress.objects.filter(student=profile, completed=True).count()
                if completed_count == 1:
                    _award('first_task', 'Перше завдання!', 'Ти виконав(ла) перше завдання. Так тримати!')
                if completed_count >= 5:
                    _award('five_tasks', '5 завдань!', 'П’ять виконаних завдань — чудовий результат!')
                if score == 100:
                    _award('perfect_score', '100%!', 'Ідеально! Усі відповіді правильні.')
            except Exception:
                pass
        except Exception:
            pass

        profile.last_exercise_type = exercise_type
        profile.last_correct = correct_count
        profile.last_total = total_questions
        profile.last_score = score
        profile.last_completed_at = timezone.now()
        profile.save(update_fields=['last_exercise_type', 'last_correct', 'last_total', 'last_score', 'last_completed_at', 'updated_at'])

    context = {
        'block': block,
        'exercise_type': exercise_type,
        'is_student': getattr(request.user, 'is_authenticated', False) and hasattr(request.user, 'student_profile'),
        'tasks_mode': True,
        'tasks_url': reverse('exercises:task_list', kwargs={'block_slug': block_slug, 'type_slug': type_slug}),
    }
    return render(request, 'exercises/quiz_result.html', context)


def quiz_print(request, block_slug, type_slug):
    """Print-friendly version of quiz for children who prefer paper"""
    tasks_limit = TASKS_LIMIT_DEFAULT
    exercise_block = get_object_or_404(ExerciseBlock, slug=block_slug)
    exercise_type = get_object_or_404(ExerciseType, block=exercise_block, slug=type_slug, is_active=True)

    variant_n = None
    try:
        n = int(request.GET.get('n', '') or 0)
        if n > 0:
            variant_n = n
    except Exception:
        variant_n = None

    questions = _select_questions_variant(exercise_type, tasks_limit, variant_n=variant_n)
    
    if not questions:
        messages.warning(request, 'Немає питань для цієї вправи')
        return redirect('exercises:type_list', block_slug=block_slug)
    
    context = {
        'block': exercise_block,
        'exercise_type': exercise_type,
        'questions': questions,
        'braille_default': request.GET.get('braille') == '1',
        'tasks_limit': tasks_limit,
    }
    return render(request, 'exercises/quiz_print.html', context)


def print_braille(request, block_slug, type_slug):
    """Backward-compatible route: redirect to the print view with Braille enabled."""
    url = reverse('exercises:quiz_print', kwargs={'block_slug': block_slug, 'type_slug': type_slug})
    return redirect(f'{url}?braille=1')


def quiz_submit(request, block_slug, type_slug):
    """Process quiz submission"""
    if request.method != 'POST':
        return redirect('exercises:quiz', block_slug=block_slug, type_slug=type_slug)
    
    exercise_block = get_object_or_404(ExerciseBlock, slug=block_slug)
    exercise_type = get_object_or_404(ExerciseType, block=exercise_block, slug=type_slug)
    questions = Question.objects.filter(exercise_type=exercise_type)

    if not questions.exists():
        messages.warning(request, 'Немає питань для цієї вправи')
        return redirect('exercises:type_list', block_slug=block_slug)
    
    # Check answers
    correct_count = 0
    total_questions = questions.count()
    
    for question in questions:
        answer_key = f'answer_{question.id}'
        user_answer = request.POST.get(answer_key, '').strip()
        if user_answer.lower() == question.correct_answer.lower():
            correct_count += 1
    
    # Calculate score
    score = (correct_count / total_questions * 100) if total_questions > 0 else 0

    # Save stats only for registered/logged-in students (shown in profile, not here)
    if getattr(request, 'user', None) and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        profile.last_exercise_type = exercise_type
        profile.last_correct = correct_count
        profile.last_total = total_questions
        profile.last_score = int(round(score))
        profile.last_completed_at = timezone.now()
        profile.save(update_fields=['last_exercise_type', 'last_correct', 'last_total', 'last_score', 'last_completed_at', 'updated_at'])

    context = {
        'block': exercise_block,
        'exercise_type': exercise_type,
        'is_student': getattr(request.user, 'is_authenticated', False) and hasattr(request.user, 'student_profile'),
    }
    return render(request, 'exercises/quiz_result.html', context)


# Legacy views
def exercise_list(request):
    categories = ExerciseCategory.objects.all()
    category_slug = request.GET.get('category')
    
    exercises = Exercise.objects.filter(is_active=True)
    if category_slug:
        exercises = exercises.filter(category__slug=category_slug)
    
    context = {
        'exercises': exercises.order_by('difficulty', 'title'),
        'categories': categories,
        'selected_category': category_slug,
    }
    return render(request, 'exercises/list.html', context)


def exercise_detail(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk, is_active=True)
    
    student_profile = None
    if hasattr(request.user, 'student_profile'):
        student_profile = request.user.student_profile
    
    previous_attempts = []
    if student_profile:
        previous_attempts = StudentProgress.objects.filter(
            student=student_profile,
            exercise=exercise
        ).order_by('-created_at')[:5]
    
    context = {
        'exercise': exercise,
        'student_profile': student_profile,
        'previous_attempts': previous_attempts,
    }
    return render(request, 'exercises/detail.html', context)


def exercise_submit(request, pk):
    if request.method != 'POST':
        return redirect('exercises:detail', pk=pk)
    
    exercise = get_object_or_404(Exercise, pk=pk, is_active=True)
    
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Тільки учні можуть виконувати вправи')
        return redirect('exercises:detail', pk=pk)
    
    student_profile = request.user.student_profile
    answer = request.POST.get('answer', '').strip()
    
    content = exercise.content or {}
    correct_answer = content.get('correct_answer', '')
    is_correct = answer.lower() == str(correct_answer).lower()
    
    score = 100.0 if is_correct else 0.0
    
    progress, created = StudentProgress.objects.get_or_create(
        student=student_profile,
        exercise=exercise,
        defaults={
            'attempts': 0,
            'correct': 0,
            'time_spent': 0,
            'score': 0,
        }
    )
    
    progress.attempts += 1
    if is_correct:
        progress.correct += 1
        progress.completed = True
        progress.score = max(progress.score, score)
        
        stars_earned = exercise.difficulty * 10
        student_profile.stars += stars_earned
        student_profile.save()
        
        messages.success(request, f'Правильно! Ви отримали {stars_earned} зірочок!')
    else:
        messages.error(request, f'Неправильно. Спробуйте ще раз!')
    
    progress.save()
    
    return redirect('exercises:detail', pk=pk)
