# Generated by Django 2.2.11 on 2020-04-03 12:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coredata', '0022_add_new_visit_data'),
        ('quizzes', '0003_update_constraint'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='timespecialcase',
            unique_together={('quiz', 'student')},
        ),
    ]
