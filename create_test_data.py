import os
import django
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "includoland.settings")
    django.setup()

from django.contrib.auth import get_user_model
from exercises.models import ExerciseBlock, ExerciseType, Question, ExerciseCategory, Exercise
from students.models import StudentProfile
from progress.models import StudentProgress
from ml_engine.models import StudentAnalytics, Recommendation
from achievements.models import Achievement, StudentAchievement, Reward
from core.models import User

# --- USERS ---
User = get_user_model()
student_user, _ = User.objects.get_or_create(username='student', defaults={
    'email': 'student@example.com', 'role': 'student', 'is_active': True
})
teacher_user, _ = User.objects.get_or_create(username='teacher', defaults={
    'email': 'teacher@example.com', 'role': 'teacher', 'is_active': True
})
parent_user, _ = User.objects.get_or_create(username='parent', defaults={
    'email': 'parent@example.com', 'role': 'parent', 'is_active': True
})
admin_user, _ = User.objects.get_or_create(username='admin', defaults={
    'email': 'admin@example.com', 'role': 'admin', 'is_superuser': True, 'is_staff': True, 'is_active': True
})

# --- STUDENT PROFILES ---
student_profile, _ = StudentProfile.objects.get_or_create(user=student_user, defaults={
    'age': 8, 'grade': '2', 'level': 1, 'stars': 0
})

# --- BLOCKS ---
math_block, _ = ExerciseBlock.objects.get_or_create(
    slug='mathematics', defaults={'name': 'Математика', 'description': 'Вправи з арифметики', 'icon': 'bi-calculator', 'color': 'primary', 'order': 1})
lang_block, _ = ExerciseBlock.objects.get_or_create(
    slug='language', defaults={'name': 'Мова', 'description': 'Вивчення мови', 'icon': 'bi-book', 'color': 'success', 'order': 2})
logic_block, _ = ExerciseBlock.objects.get_or_create(
    slug='logic', defaults={'name': 'Логіка', 'description': 'Логічне мислення', 'icon': 'bi-puzzle', 'color': 'info', 'order': 3})

# --- EXERCISE TYPES ---
addition, _ = ExerciseType.objects.get_or_create(slug='addition', block=math_block, defaults={'name': 'Додавання', 'description': 'Вчимося додавати', 'difficulty': 1})
subtraction, _ = ExerciseType.objects.get_or_create(slug='subtraction', block=math_block, defaults={'name': 'Віднімання', 'description': 'Вчимося віднімати', 'difficulty': 2})
letters, _ = ExerciseType.objects.get_or_create(slug='letters', block=lang_block, defaults={'name': 'Літери', 'description': 'Вивчаємо літери', 'difficulty': 1})
sequences, _ = ExerciseType.objects.get_or_create(slug='sequences', block=logic_block, defaults={'name': 'Послідовності', 'description': 'Знаходимо закономірності', 'difficulty': 2})

# --- QUESTIONS ---
for q in [
    {'type': addition, 'text': '1 + 1 = ?', 'answer': '2'},
    {'type': addition, 'text': '2 + 2 = ?', 'answer': '4'},
    {'type': addition, 'text': '3 + 2 = ?', 'answer': '5'},
    {'type': addition, 'text': '5 + 5 = ?', 'answer': '10'},
    {'type': addition, 'text': '4 + 3 = ?', 'answer': '7'},
    {'type': subtraction, 'text': '5 - 1 = ?', 'answer': '4'},
    {'type': subtraction, 'text': '10 - 5 = ?', 'answer': '5'},
    {'type': subtraction, 'text': '8 - 3 = ?', 'answer': '5'},
    {'type': subtraction, 'text': '7 - 2 = ?', 'answer': '5'},
    {'type': letters, 'text': 'Яка перша літера у слові КІТ?', 'answer': 'К'},
    {'type': letters, 'text': 'Яка остання літера у слові КІТ?', 'answer': 'Т'},
    {'type': letters, 'text': 'Яка літера посередині у слові КІТ?', 'answer': 'І'},
    {'type': sequences, 'text': 'Яке наступне число: 2, 4, 6, 8, ?', 'answer': '10'},
    {'type': sequences, 'text': 'Яке наступне число: 1, 3, 5, 7, ?', 'answer': '9'},
    {'type': sequences, 'text': 'Яке наступне число: 10, 20, 30, ?', 'answer': '40'},
]:
    Question.objects.get_or_create(exercise_type=q['type'], question_text=q['text'], defaults={'correct_answer': q['answer']})

# --- EXERCISE CATEGORIES & EXERCISES ---
cat_math, _ = ExerciseCategory.objects.get_or_create(slug='math', defaults={'name': 'Математика'})
cat_lang, _ = ExerciseCategory.objects.get_or_create(slug='lang', defaults={'name': 'Мова'})
ex1, _ = Exercise.objects.get_or_create(title='Додати 2 і 3', category=cat_math, defaults={'content': {'correct_answer': '5'}, 'difficulty': 1})
ex2, _ = Exercise.objects.get_or_create(title='Відняти 4 з 7', category=cat_math, defaults={'content': {'correct_answer': '3'}, 'difficulty': 2})
ex3, _ = Exercise.objects.get_or_create(title='Перша літера у слові ДІМ', category=cat_lang, defaults={'content': {'correct_answer': 'Д'}, 'difficulty': 1})

# --- STUDENT PROGRESS ---
StudentProgress.objects.get_or_create(student=student_profile, exercise=ex1, defaults={'attempts': 1, 'correct': 1, 'score': 100, 'completed': True})
StudentProgress.objects.get_or_create(student=student_profile, exercise_type=addition, defaults={'attempts': 2, 'correct': 2, 'score': 100, 'completed': True})

# --- ANALYTICS & RECOMMENDATIONS ---
StudentAnalytics.objects.get_or_create(student=student_profile, defaults={'data': {'avg_score': 95}})
Recommendation.objects.get_or_create(student=student_profile, exercise=ex2, defaults={'reason': 'Потрібно покращити віднімання'})

# --- ACHIEVEMENTS & REWARDS ---
ach1, _ = Achievement.objects.get_or_create(code='first_quiz', defaults={'title': 'Перша вікторина', 'description': 'Пройдено першу вікторину'})
StudentAchievement.objects.get_or_create(achievement=ach1, student=student_profile)
Reward.objects.get_or_create(name='Кольоровий олівець', cost=10, description='Можна обміняти на 10 зірочок')

print('Тестові дані для всіх моделей успішно створені!')

# Create Math block
math_block, created = ExerciseBlock.objects.get_or_create(
    slug='mathematics',
    defaults={
        'name': 'Математика',
        'description': 'Вправи з арифметики, логіки та рахунку',
        'icon': 'bi-calculator',
        'color': 'primary',
        'order': 1
    }
)
print(f"Math block: {'created' if created else 'exists'}")

# Create Language block
lang_block, created = ExerciseBlock.objects.get_or_create(
    slug='language',
    defaults={
        'name': 'Мова',
        'description': 'Вивчення літер, слів та читання',
        'icon': 'bi-book',
        'color': 'success',
        'order': 2
    }
)
print(f"Language block: {'created' if created else 'exists'}")

# Create Logic block
logic_block, created = ExerciseBlock.objects.get_or_create(
    slug='logic',
    defaults={
        'name': 'Логіка',
        'description': 'Розвиток логічного мислення та пам\'яті',
        'icon': 'bi-puzzle',
        'color': 'info',
        'order': 3
    }
)
print(f"Logic block: {'created' if created else 'exists'}")

# Create Exercise Types
# Math - Addition
addition, created = ExerciseType.objects.get_or_create(
    slug='addition',
    block=math_block,
    defaults={
        'name': 'Додавання',
        'description': 'Вчимося додавати числа',
        'difficulty': 1
    }
)
print(f"Addition type: {'created' if created else 'exists'}")

# Create questions for Addition
questions_data = [
    {'text': '1 + 1 = ?', 'answer': '2'},
    {'text': '2 + 2 = ?', 'answer': '4'},
    {'text': '3 + 2 = ?', 'answer': '5'},
    {'text': '5 + 5 = ?', 'answer': '10'},
    {'text': '4 + 3 = ?', 'answer': '7'},
]

for q_data in questions_data:
    q, created = Question.objects.get_or_create(
        exercise_type=addition,
        question_text=q_data['text'],
        defaults={'correct_answer': q_data['answer']}
    )
    if created:
        print(f"Question created: {q_data['text']}")

# Math - Subtraction
subtraction, created = ExerciseType.objects.get_or_create(
    slug='subtraction',
    block=math_block,
    defaults={
        'name': 'Віднімання',
        'description': 'Вчимося віднімати числа',
        'difficulty': 2
    }
)
print(f"Subtraction type: {'created' if created else 'exists'}")

subtraction_questions = [
    {'text': '5 - 1 = ?', 'answer': '4'},
    {'text': '10 - 5 = ?', 'answer': '5'},
    {'text': '8 - 3 = ?', 'answer': '5'},
    {'text': '7 - 2 = ?', 'answer': '5'},
]

for q_data in subtraction_questions:
    q, created = Question.objects.get_or_create(
        exercise_type=subtraction,
        question_text=q_data['text'],
        defaults={'correct_answer': q_data['answer']}
    )
    if created:
        print(f"Question created: {q_data['text']}")

# Language - Letters
letters, created = ExerciseType.objects.get_or_create(
    slug='letters',
    block=lang_block,
    defaults={
        'name': 'Літери',
        'description': 'Вивчаємо літери алфавіту',
        'difficulty': 1
    }
)
print(f"Letters type: {'created' if created else 'exists'}")

letter_questions = [
    {'text': 'Яка перша літера у слові КІТ?', 'answer': 'К'},
    {'text': 'Яка остання літера у слові КІТ?', 'answer': 'Т'},
    {'text': 'Яка літера посередині у слові КІТ?', 'answer': 'І'},
]

for q_data in letter_questions:
    q, created = Question.objects.get_or_create(
        exercise_type=letters,
        question_text=q_data['text'],
        defaults={'correct_answer': q_data['answer']}
    )
    if created:
        print(f"Question created: {q_data['text']}")

# Logic - Sequences
sequences, created = ExerciseType.objects.get_or_create(
    slug='sequences',
    block=logic_block,
    defaults={
        'name': 'Послідовності',
        'description': 'Знаходимо закономірності в числах',
        'difficulty': 2
    }
)
print(f"Sequences type: {'created' if created else 'exists'}")

sequence_questions = [
    {'text': 'Яке наступне число: 2, 4, 6, 8, ?', 'answer': '10'},
    {'text': 'Яке наступне число: 1, 3, 5, 7, ?', 'answer': '9'},
    {'text': 'Яке наступне число: 10, 20, 30, ?', 'answer': '40'},
]

for q_data in sequence_questions:
    q, created = Question.objects.get_or_create(
        exercise_type=sequences,
        question_text=q_data['text'],
        defaults={'correct_answer': q_data['answer']}
    )
    if created:
        print(f"Question created: {q_data['text']}")

print("\nДані успішно створені!")
print(f"Блоків: {ExerciseBlock.objects.count()}")
print(f"Типів вправ: {ExerciseType.objects.count()}")
print(f"Питань: {Question.objects.count()}")
