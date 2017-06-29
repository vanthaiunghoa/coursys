# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-28 12:26
from __future__ import unicode_literals

from django.db import migrations, models
import relationships.handlers


class Migration(migrations.Migration):

    dependencies = [
        ('relationships', '0002_add_attachments'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='company_name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('employer', relationships.handlers.EmployerEvent), ('photo', relationships.handlers.PhotoEvent), ('quote', relationships.handlers.QuoteEvent), ('resume', relationships.handlers.ResumeEvent)], max_length=10),
        ),
    ]
