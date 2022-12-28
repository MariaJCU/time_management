from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
import pytz
from tinymce import models as tinymce_models


# Create your models here.

class tasks(models.Model):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=500)
    label = models.CharField(max_length=500, default="None")
    comple_sta = models.BooleanField(default=False)
    tracking_sta = models.BooleanField(default=False)
    assigned_date = models.DateField(default=timezone.now)
    creation_date = models.DateTimeField(auto_now_add=True)
    description = tinymce_models.HTMLField(default="None")


class work_periods(models.Model):
    task_id = models.ForeignKey(tasks, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True)
    finish_time = models.DateTimeField(null=True)
    total_time = models.DecimalField(max_digits=5, decimal_places=2, null=True)


class profile(models.Model):
    TIMEZONES = tuple(zip(pytz.common_timezones, pytz.common_timezones))

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=32, choices=TIMEZONES, default='UTC')


class month_note(models.Model):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notes = tinymce_models.HTMLField(default="None")