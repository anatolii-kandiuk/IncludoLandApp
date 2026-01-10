from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0002_studentprofile_last_stats'),
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
        WHERE table_name = 'students_studentprofile' AND column_name = 'grade'
    ) THEN
        ALTER TABLE students_studentprofile ALTER COLUMN grade SET DEFAULT 1;
        UPDATE students_studentprofile SET grade = 1 WHERE grade IS NULL;
        ALTER TABLE students_studentprofile ALTER COLUMN grade SET NOT NULL;
    END IF;
END $$;
""",
                    reverse_sql="""
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'students_studentprofile' AND column_name = 'grade'
    ) THEN
        ALTER TABLE students_studentprofile ALTER COLUMN grade DROP DEFAULT;
    END IF;
END $$;
""",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='studentprofile',
                    name='grade',
                    field=models.PositiveSmallIntegerField(default=1),
                ),
            ],
        )
    ]
