# Generated by Django 5.0.6 on 2024-06-24 04:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('camera', '0002_ddnscamera_stream_url_staticcamera_stream_url'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ddnscamera',
            name='stream_url',
        ),
        migrations.RemoveField(
            model_name='staticcamera',
            name='stream_url',
        ),
        migrations.CreateModel(
            name='CameraStream',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stream_url', models.CharField(max_length=255)),
                ('camera', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='camera.staticcamera')),
                ('ddns_camera', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='camera.ddnscamera')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]