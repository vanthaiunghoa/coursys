# Generated by Django 2.2.11 on 2020-04-28 13:55

import courselib.json_fields
import django.core.files.storage
from django.db import migrations, models
import marking.models


class Migration(migrations.Migration):

    dependencies = [
        ('marking', '0007_on_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitycomponent',
            name='config',
            field=courselib.json_fields.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='activitymark',
            name='file_attachment',
            field=models.FileField(blank=True, max_length=500, null=True, storage=django.core.files.storage.FileSystemStorage(base_url=None, file_permissions_mode=420, location='submitted_files'), upload_to=marking.models.attachment_upload_to),
        ),
    ]