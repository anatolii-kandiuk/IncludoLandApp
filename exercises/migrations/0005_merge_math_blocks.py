from django.db import migrations


def merge_math_blocks(apps, schema_editor):
    ExerciseBlock = apps.get_model('exercises', 'ExerciseBlock')
    ExerciseType = apps.get_model('exercises', 'ExerciseType')

    canonical = ExerciseBlock.objects.filter(slug='mathematics').first()
    duplicate = ExerciseBlock.objects.filter(slug='math').first()

    if not canonical or not duplicate or canonical.id == duplicate.id:
        return

    # Move types from duplicate -> canonical, avoiding slug collisions.
    existing_slugs = set(
        ExerciseType.objects.filter(block=canonical).values_list('slug', flat=True)
    )

    for t in ExerciseType.objects.filter(block=duplicate):
        if t.slug in existing_slugs:
            # Skip on collision (shouldn't happen in current data).
            continue
        t.block_id = canonical.id
        t.save(update_fields=['block'])
        existing_slugs.add(t.slug)

    duplicate.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('exercises', '0004_fix_mathematics_block_name'),
    ]

    operations = [
        migrations.RunPython(merge_math_blocks, migrations.RunPython.noop),
    ]
