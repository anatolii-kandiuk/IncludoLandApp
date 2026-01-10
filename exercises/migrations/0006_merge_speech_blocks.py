from django.db import migrations


def merge_speech_blocks(apps, schema_editor):
    ExerciseBlock = apps.get_model('exercises', 'ExerciseBlock')
    ExerciseType = apps.get_model('exercises', 'ExerciseType')

    source_slugs = ['language', 'letters', 'words']

    # Create/normalize destination block
    speech, _ = ExerciseBlock.objects.get_or_create(
        slug='speech',
        defaults={
            'name': 'Мовлення',
            'description': 'Вправи з мовлення',
            'icon': 'bi-chat-dots',
            'color': 'primary',
            'order': 2,
        },
    )
    if speech.name != 'Мовлення':
        speech.name = 'Мовлення'
        speech.save(update_fields=['name'])

    existing_type_slugs = set(
        ExerciseType.objects.filter(block=speech).values_list('slug', flat=True)
    )

    # Move types from source blocks into the destination block
    sources = list(ExerciseBlock.objects.filter(slug__in=source_slugs).order_by('id'))
    for src in sources:
        for t in ExerciseType.objects.filter(block=src).order_by('id'):
            new_slug = t.slug
            if new_slug in existing_type_slugs:
                # Ensure uniqueness within the destination block
                base = new_slug
                i = 2
                while new_slug in existing_type_slugs:
                    new_slug = f"{base}-{i}"
                    i += 1
                t.slug = new_slug

            t.block_id = speech.id
            t.save(update_fields=['block', 'slug'])
            existing_type_slugs.add(t.slug)

    # Delete now-empty source blocks
    for src in sources:
        if not ExerciseType.objects.filter(block=src).exists():
            src.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('exercises', '0005_merge_math_blocks'),
    ]

    operations = [
        migrations.RunPython(merge_speech_blocks, migrations.RunPython.noop),
    ]
