from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0004_studentprofile_state_sync'),
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
        ALTER TABLE students_studentprofile DROP COLUMN grade;
    END IF;
END $$;
""",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='studentprofile',
                    name='grade',
                ),
            ],
        )
    ]
