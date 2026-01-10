from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_studentprofile_grade'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'students_studentprofile' AND column_name = 'special_needs'
    ) THEN
        ALTER TABLE students_studentprofile ALTER COLUMN special_needs SET DEFAULT '';
        UPDATE students_studentprofile SET special_needs = '' WHERE special_needs IS NULL;
        ALTER TABLE students_studentprofile ALTER COLUMN special_needs SET NOT NULL;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'students_studentprofile' AND column_name = 'level'
    ) THEN
        ALTER TABLE students_studentprofile ALTER COLUMN level SET DEFAULT 1;
        UPDATE students_studentprofile SET level = 1 WHERE level IS NULL;
        ALTER TABLE students_studentprofile ALTER COLUMN level SET NOT NULL;
    END IF;
END $$;
""",
                    reverse_sql="""
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'students_studentprofile' AND column_name = 'special_needs'
    ) THEN
        ALTER TABLE students_studentprofile ALTER COLUMN special_needs DROP DEFAULT;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'students_studentprofile' AND column_name = 'level'
    ) THEN
        ALTER TABLE students_studentprofile ALTER COLUMN level DROP DEFAULT;
    END IF;
END $$;
""",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='studentprofile',
                    name='age',
                    field=models.PositiveSmallIntegerField(blank=True, null=True),
                ),
                migrations.AlterField(
                    model_name='studentprofile',
                    name='grade',
                    field=models.CharField(default='1', max_length=10),
                ),
                migrations.AddField(
                    model_name='studentprofile',
                    name='special_needs',
                    field=models.TextField(blank=True, default=''),
                ),
                migrations.AddField(
                    model_name='studentprofile',
                    name='level',
                    field=models.PositiveSmallIntegerField(default=1),
                ),
            ],
        )
    ]
