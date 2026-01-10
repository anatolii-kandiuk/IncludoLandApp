from django.contrib.auth import get_user_model
from students.models import StudentProfile
from django.contrib.auth.models import Group

User = get_user_model()

def create_students_and_teacher():
    # Create teacher
    teacher, created = User.objects.get_or_create(username='teacher1', defaults={
        'email': 'teacher1@example.com',
        'is_staff': True,
        'is_superuser': False,
    })
    if created:
        teacher.set_password('teacherpass')
        teacher.save()
        print('Teacher created')
    else:
        print('Teacher already exists')

    # Create students
    for i in range(2, 5):
        username = f'student{i}'
        email = f'student{i}@example.com'
        user, created = User.objects.get_or_create(username=username, defaults={
            'email': email,
            'is_staff': False,
            'is_superuser': False,
        })
        if created:
            user.set_password(f'studentpass{i}')
            user.save()
            StudentProfile.objects.get_or_create(user=user)
            print(f'Student {username} created')
        else:
            print(f'Student {username} already exists')

if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'includoland.settings')
    django.setup()
    create_students_and_teacher()
