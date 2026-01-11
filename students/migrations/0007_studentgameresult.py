from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0006_audiostory_naturesound'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentGameResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game_key', models.CharField(max_length=40)),
                ('game_name', models.CharField(max_length=80)),
                ('score', models.PositiveSmallIntegerField(default=0)),
                ('played_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_results', to='students.studentprofile')),
            ],
            options={
                'ordering': ['-played_at', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='studentgameresult',
            index=models.Index(fields=['student', 'game_key', 'played_at'], name='students_st_student_ae2524_idx'),
        ),
    ]
