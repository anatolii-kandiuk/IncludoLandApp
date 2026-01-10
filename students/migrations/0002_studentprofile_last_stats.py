from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0003_seed_default_blocks'),
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='last_completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='last_correct',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='last_exercise_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='exercises.exercisetype'),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='last_score',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='last_total',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
