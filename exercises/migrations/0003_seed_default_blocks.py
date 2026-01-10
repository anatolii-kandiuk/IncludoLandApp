from django.db import migrations


def seed_defaults(apps, schema_editor):
    ExerciseBlock = apps.get_model('exercises', 'ExerciseBlock')
    ExerciseType = apps.get_model('exercises', 'ExerciseType')

    defaults = [
        {
            'name': 'Математика',
            'slug': 'math',
            'description': 'Базові математичні вправи',
            'icon': 'bi-calculator',
            'color': 'primary',
            'order': 1,
            'types': [
                {'name': 'Рахування', 'slug': 'counting', 'description': 'Рахування та прості приклади', 'difficulty': 1, 'order': 1},
            ],
        },
        {
            'name': 'Букви',
            'slug': 'letters',
            'description': 'Вправи з буквами',
            'icon': 'bi-alphabet',
            'color': 'success',
            'order': 2,
            'types': [
                {'name': 'Розпізнавання букв', 'slug': 'letter-recognition', 'description': 'Вибір правильної букви', 'difficulty': 1, 'order': 1},
            ],
        },
        {
            'name': 'Слова',
            'slug': 'words',
            'description': 'Вправи зі словами',
            'icon': 'bi-chat-left-text',
            'color': 'warning',
            'order': 3,
            'types': [
                {'name': 'Складання слів', 'slug': 'word-building', 'description': 'Вибір правильного слова', 'difficulty': 2, 'order': 1},
            ],
        },
    ]

    for block_def in defaults:
        block, _ = ExerciseBlock.objects.get_or_create(
            slug=block_def['slug'],
            defaults={
                'name': block_def['name'],
                'description': block_def['description'],
                'icon': block_def['icon'],
                'color': block_def['color'],
                'order': block_def['order'],
            },
        )
        # Ensure name/description stay reasonable if existed
        if block.name != block_def['name']:
            block.name = block_def['name']
            block.save(update_fields=['name'])

        for t in block_def['types']:
            ExerciseType.objects.get_or_create(
                block=block,
                slug=t['slug'],
                defaults={
                    'name': t['name'],
                    'description': t['description'],
                    'difficulty': t['difficulty'],
                    'order': t['order'],
                    'is_active': True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ('exercises', '0002_exerciseblock_exercisetype_question'),
    ]

    operations = [
        migrations.RunPython(seed_defaults, migrations.RunPython.noop),
    ]
