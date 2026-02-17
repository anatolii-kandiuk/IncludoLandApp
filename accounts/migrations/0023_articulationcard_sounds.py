from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0022_specialist_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='articulationcard',
            name='sounds',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
