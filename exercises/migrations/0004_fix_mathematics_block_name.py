from django.db import migrations


def fix_mathematics_block_name(apps, schema_editor):
    ExerciseBlock = apps.get_model('exercises', 'ExerciseBlock')

    # Some environments have a pre-existing block with slug 'mathematics'
    # but an incorrect name (e.g. 'content'). Normalize it.
    ExerciseBlock.objects.filter(slug='mathematics').update(name='Математика')


class Migration(migrations.Migration):
    dependencies = [
        ('exercises', '0003_seed_default_blocks'),
    ]

    operations = [
        migrations.RunPython(fix_mathematics_block_name, migrations.RunPython.noop),
    ]
