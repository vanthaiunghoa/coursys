# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_auto_20150722_0958'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hardcodedreport',
            name='file_location',
            field=models.CharField(help_text=b'The location of this report, on disk.', max_length=80, choices=[(b'majors_in_courses.py', b'majors_in_courses.py'), (b'ensc_150_and_250_but_not_215.py', b'ensc_150_and_250_but_not_215.py'), (b'immediate_retake_report.py', b'immediate_retake_report.py'), (b'fas_international.py', b'fas_international.py'), (b'five_retakes.py', b'five_retakes.py'), (b'cmpt165_after_cmpt.py', b'cmpt165_after_cmpt.py'), (b'low_gpa_or_no_coop.py', b'low_gpa_or_no_coop.py'), (b'mse_410_less_than_3_coops.py', b'mse_410_less_than_3_coops.py'), (b'fake_report.py', b'fake_report.py'), (b'bad_first_semester.py', b'bad_first_semester.py'), (b'enscpro_coop.py', b'enscpro_coop.py'), (b'fas_with_email.py', b'fas_with_email.py'), (b'bad_gpas.py', b'bad_gpas.py')]),
        ),
    ]