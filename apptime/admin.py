from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import tasks, work_periods, profile


class tasksadmin(admin.ModelAdmin):
    readonly_fields = ('assigned_date', 'creation_date')


# Define an inline admin descriptor for profile model
class profileinline(admin.StackedInline):
    model = profile
    can_delete = False
    verbose_name_plural = 'profiles'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (profileinline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register your models here.
admin.site.register(tasks, tasksadmin)
admin.site.register(work_periods)