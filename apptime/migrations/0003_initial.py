# Generated by Django 4.0.5 on 2022-07-11 20:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('apptime', '0002_remove_work_periods_task_id_delete_tasks_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='tasks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_name', models.CharField(max_length=500)),
                ('label', models.IntegerField()),
                ('comple_sta', models.BooleanField(default=False)),
                ('tracking_sta', models.BooleanField(default=False)),
                ('assigned_date', models.DateTimeField()),
                ('creation_date', models.DateTimeField()),
                ('description', models.TextField()),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='work_periods',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('finish_time', models.DateTimeField()),
                ('total_time', models.DecimalField(decimal_places=2, max_digits=5)),
                ('task_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apptime.tasks')),
            ],
        ),
    ]
