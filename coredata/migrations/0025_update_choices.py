# Generated by Django 2.2.22 on 2021-05-20 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coredata', '0024_longer_userid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='combinedoffering',
            name='component',
            field=models.CharField(choices=[('LEC', 'Lecture'), ('LAB', 'Lab'), ('TUT', 'Tutorial'), ('SEM', 'Seminar'), ('SEC', 'Section'), ('PRA', 'Practicum'), ('IND', 'Individual Work'), ('INS', 'INS'), ('WKS', 'Workshop'), ('FLD', 'Field School'), ('STD', 'Studio'), ('OLC', 'OLC'), ('RQL', 'RQL'), ('RSC', 'RSC'), ('STL', 'STL'), ('CNV', 'CNV'), ('OPL', 'Open Lab'), ('EXM', 'Exam'), ('CAP', 'Capstone Required'), ('INT', 'Internship Required'), ('CAP', 'Capstone'), ('COP', 'Work Integrated Learning'), ('THE', 'Thesis Research'), ('PHC', 'Unknown'), ('PHF', 'Placeholder'), ('CAN', 'Cancelled')], max_length=3),
        ),
        migrations.AlterField(
            model_name='courseoffering',
            name='component',
            field=models.CharField(choices=[('LEC', 'Lecture'), ('LAB', 'Lab'), ('TUT', 'Tutorial'), ('SEM', 'Seminar'), ('SEC', 'Section'), ('PRA', 'Practicum'), ('IND', 'Individual Work'), ('INS', 'INS'), ('WKS', 'Workshop'), ('FLD', 'Field School'), ('STD', 'Studio'), ('OLC', 'OLC'), ('RQL', 'RQL'), ('RSC', 'RSC'), ('STL', 'STL'), ('CNV', 'CNV'), ('OPL', 'Open Lab'), ('EXM', 'Exam'), ('CAP', 'Capstone Required'), ('INT', 'Internship Required'), ('CAP', 'Capstone'), ('COP', 'Work Integrated Learning'), ('THE', 'Thesis Research'), ('PHC', 'Unknown'), ('PHF', 'Placeholder'), ('CAN', 'Cancelled')], db_index=True, help_text='Component of the offering, like "LEC" or "LAB"', max_length=3),
        ),
    ]