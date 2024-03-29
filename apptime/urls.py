from atexit import register
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name = "index"),
    path("login_pg", views.login_pg, name = "login_pg"),
    path("register", views.register, name = "register"),
    path("agenda/<int:year>/<int:month>/<int:day>", views.agenda, name = "agenda"),
    path("time_tracking", views.time_tracking, name = "time_tracking"),
    path("start_task", views.start_task, name = "start_task"),
    path("log_time", views.log_time, name = "log_time"),
    path("logout_view", views.logout_view, name = "logout_view"),
    path("taskinfo/<int:year>/<int:month>/<int:day>/<int:task_id>", views.taskinfo, name="taskinfo"),
    path("create_task/<str:date>", views.create_task, name="create_task"),
    path("edit_task/<int:year>/<int:month>/<int:day>/<int:task_id>", views.edit_task, name="edit_task"),
    path("account", views.account, name="account"),
    path('task_autocomplete', views.task_autocomplete, name='task_autocomplete'),
    path('label_autocomplete', views.label_autocomplete, name='label_autocomplete'),
    path('tinymce', include('tinymce.urls')),
    path('pages', include('django.contrib.flatpages.urls')),
    path('month_calendar/<int:year>/<int:month>/<int:day>', views.month_calendar, name='month_calendar')
]