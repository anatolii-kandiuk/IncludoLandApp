from django.db import migrations, models


def map_existing_roles(apps, schema_editor):
    User = apps.get_model('core', 'User')
    User.objects.filter(role='student').update(role='child')
    User.objects.filter(role='teacher').update(role='specialist')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('child', 'Дитина'),
                    ('specialist', 'Спеціаліст'),
                    ('parent', 'Батько/Мати'),
                    ('admin', 'Адмін'),
                ],
                default='child',
                max_length=20,
            ),
        ),
        migrations.RunPython(map_existing_roles, migrations.RunPython.noop),
    ]
