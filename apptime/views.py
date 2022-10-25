from datetime import datetime, timedelta
import re
import pytz
from pprint import pprint
import mimetypes
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, Paragraph
import math
from reportlab.platypus import BaseDocTemplate
from reportlab.lib.styles import getSampleStyleSheet
import json


from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from apptime.models import tasks, work_periods, profile
from .forms import NewUserForm, loginform, start_task_form, log_prev_time_form, agenda_form, task_full_form, time_filter_form, file_form, account_form, timezoneform
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.messages import get_messages
from django.urls import reverse
from django.db import connection, connections, transaction
from django.utils import timezone
from django.db.models import F, Sum

# Global variables
TIMEZONES = pytz.common_timezones
DICFILTER = {}
# These variables are used as display formats for the tamplates' |date filter
DATEFORMAT = 'D, N j, Y'
DATETIMEFORMAT = 'N j, Y h:m a'

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        print(user_id)

        # if user is logged in change the time zone to the one in the user's database
        zone_query = profile.objects.select_related('user').get(user_id=user_id)

        request.session['django_timezone'] = zone_query.timezone

        return HttpResponseRedirect("agenda")
    else:
        return HttpResponseRedirect("login_pg")


def login_pg(request):
    if request.method == "POST":
        form = loginform(request.POST)
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        messages.error(request, "Could not log in. Invalid information.") 

    form = loginform()
    return render(request=request, template_name="apptime/login.html", context={"login_form":form})


def register(request):
    if request.method == "POST":
            form = NewUserForm(request.POST)
            formzone = timezoneform(request.POST)

            if form.is_valid() and formzone.is_valid():
                # log user
                user = form.save()
                login(request, user)

                # create a timezone profile in database
                zone=request.POST["timezone"]
                userid=request.user.id
                profilechange = profile(timezone=zone, user_id=userid)
                profilechange.save()

                return HttpResponseRedirect("agenda")
            messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    formzone = timezoneform()
    return render(request=request, template_name="apptime/register.html", context={"register_form":form, "timezoneform":formzone})
            

def logout_view(request):
    logout(request)
    return HttpResponseRedirect("login_pg") 


@login_required(login_url='login_pg')
def account(request):
    # look for the user's info
    user_query = profile.objects.select_related('user').filter(user_id=request.user.id).values('user__username', 'user__email', 'user__date_joined', 'timezone')

    if request.method == 'POST':

        # Chage user's settings
        if request.POST.get('account_edit') == 't':
            form = account_form(request.POST)
            if form.is_valid():
                #get user entered values
                zone = form.cleaned_data.get("timezone")
                username = form.cleaned_data.get("username")
                email = form.cleaned_data.get("email")

                # create dict of elements to update
                filter_kwargs = {}
                dictionary = {'username': username, 'email': email}
                for key, value in dictionary.items():
                    if value:
                        filter_kwargs[key] = value
            
                with transaction.atomic():
                    User.objects.filter(id=request.user.id).update(**filter_kwargs)
                    if zone:
                        # set the session's timezone
                        request.session['django_timezone'] = zone

                        #update the timezone in database
                        profile.objects.filter(user_id=request.user.id).update(timezone=zone)

                messages.success(request, 'Your information was successfully updated!')

            else:
                messages.error(request, "Could not update settings. Invalid information.")

            return redirect('account')
                

        # change user's password
        if request.POST.get('password_edit') == 't':
            formpass = PasswordChangeForm(user=request.user, data=request.POST)

            if formpass.is_valid():
                formpass.save()
                update_session_auth_hash(request, formpass.user)
                messages.success(request, 'Your password was successfully updated!')
                
            else:
                messages.error(request, "Could not update password. Invalid information.") 

            return redirect('account')

        # check which bottom was pressed
        if request.POST.get('edit_account') == 't':
            edit = 1
        else:
            edit = 0

        #get form
        print(user_query[0]['timezone'])
        form = account_form(initial={'username': user_query[0]['user__username'], 'email':user_query[0]['user__email'], 'timezone':user_query[0]['timezone']})
        formpass = PasswordChangeForm(user=request.user, data=request.POST)
        return render(request, 'apptime/account.html', context={'timezones': TIMEZONES,'account_form':form, 'edit':edit, 'PasswordChangeForm':formpass})

    return render(request, 'apptime/account.html', context={'timezones': TIMEZONES, 'UserDic':user_query[0]})


@login_required(login_url='login_pg')
def create_task(request, date):
    # create the desired task
    task = request.POST["task"]
    label = request.POST["label"]
    assigned = request.POST["assigned"]
    if not assigned:
        assigned = date

    description = request.POST["description"]

    # get user's object
    userobj = User.objects.get(id=request.user.id)

    # Create task / insert it in the tasks table
    task_to_insert = tasks(user_id = userobj, task_name = task, label = label, assigned_date = assigned, description = description)
    task_to_insert.save()

    return 0


@login_required(login_url='login_pg')
def agenda(request):
    task_form = task_full_form()

    if request.method == "POST":
            if request.POST.get('agendaback') == 't':
                now = request.POST["sunday"]
                #debugging
                """
                print("CHECKING FORMATS:", now)
                print("CHECKING TYPES:", type(now))
                """

                now = datetime.strptime(now, '%Y-%m-%d')
                form = agenda_form()

                # Find the Sunday of the last week
                now = now - timedelta(days=7)

                # Create a dic with the respective dates
                datesdic = calc_week(now, None)

                # Get the user's tasks from the respective week
                tasklist = find_tasks_for_week(request.user.id, datesdic, None)

                # Display the tasks
                return render(request, "apptime/agenda.html", context={"datesdic":datesdic, "tasklist":tasklist, "agenda_form":form, "task_full_form":task_form, 'format':DATEFORMAT})

            elif request.POST.get('agendaforward') == 't':
                now = request.POST["sunday"]
                now = datetime.strptime(now, '%Y-%m-%d')
                form = agenda_form()

                # Find the Sunday of next week
                now = now + timedelta(days=7)

                # Create a dic with the respective dates
                datesdic = calc_week(now, None)

                # Get the user's tasks from the respective week
                tasklist = find_tasks_for_week(request.user.id, datesdic, None)

                # Display the tasks
                return render(request, "apptime/agenda.html", context={"datesdic":datesdic, "tasklist":tasklist, "agenda_form":form, "task_full_form":task_form, 'format':DATEFORMAT})

            elif request.POST.get('date_entered') == 't':
                form = agenda_form(request.POST)
                now = request.POST["agendadate"]
                now = datetime.strptime(now, '%Y-%m-%d')
                day = now.weekday()

                # find last Sunday
                while not (day == 6):
                    now = now - timedelta(days=1)
                    day = now.weekday()

                # create dic with the dates of the week
                datesdic = calc_week(now, None)

                # Get the tasks for the week
                tasklist = find_tasks_for_week(request.user.id, datesdic, None)

                return render(request, "apptime/agenda.html", context={"datesdic":datesdic, "tasklist":tasklist, "agenda_form":form, "task_full_form":task_form, 'format':DATEFORMAT})

            elif request.POST.get('add_date'):
                add_date = request.POST.get('add_date')

                # add_date has the following format before converting: "Oct. 16, 2022"
                # conver add_date to datetime
                format = "%b. %d, %Y" 
                add_date = datetime.strptime(add_date, format)

                create_task(request, add_date)


            elif request.POST.get('tracking_sta') == 't':
                task_id = request.POST.get('task_id')

                # find the incomplete work period of given task_id
                start_time = work_periods.objects.raw('''SELECT apptime_work_periods.id, apptime_work_periods.start_time
                                                            FROM apptime_work_periods 
                                                            JOIN apptime_tasks ON apptime_work_periods.task_id_id = apptime_tasks.id
                                                            WHERE apptime_work_periods.task_id_id = %s 
                                                            AND apptime_tasks.user_id_id = %s
                                                            AND apptime_work_periods.finish_time IS NULL''', (task_id, request.user.id))
                finish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                complete_period(start_time[0].id, request.user.id, start_time[0].start_time.strftime("%Y-%m-%d %H:%M:%S"), finish_time)

            elif request.POST.get('tracking_sta') == 'f':
                task_id = request.POST.get('task_id')
                user_id = request.user.id
                label = None
                start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                name = tasks.objects.raw('''SELECT apptime_tasks.id, apptime_tasks.task_name
                                                FROM apptime_tasks
                                                WHERE user_id_id = %s
                                                AND id = %s''', [user_id, task_id])

                # Insert or update task and add a work period
                create_incomplete_period(user_id, task_id, name[0].task_name, label, start_time)

            elif request.POST.get('complete') == 'f':
                # chage it to true
                task_id = request.POST.get('task_id')
                user_id = request.user.id
                
                with connection.cursor() as cursor:
                    cursor.execute("""UPDATE apptime_tasks
                                        SET comple_sta = 't'
                                        WHERE apptime_tasks.user_id_id = %s AND apptime_tasks.id = %s
                                        """, (user_id, task_id))
                
            elif request.POST.get('complete') == 't':
                # change it to false
                task_id = request.POST.get('task_id')
                user_id = request.user.id
                
                with connection.cursor() as cursor:
                    cursor.execute("""UPDATE apptime_tasks
                                        SET comple_sta = 'f'
                                        WHERE apptime_tasks.user_id_id = %s AND apptime_tasks.id = %s
                                        """, (user_id, task_id))
            

    now = datetime.now()
    day = now.weekday()
    form = agenda_form()

    # find last Sunday
    while not (day == 6):
        now = now - timedelta(days=1)
        day = now.weekday()

    # create dic with the dates of the week
    datesdic = calc_week(now, None)

    # Get the tasks for the week
    tasklist = find_tasks_for_week(request.user.id, datesdic, None)

    return render(request, "apptime/agenda.html", context={
        "datesdic":datesdic, 
        "tasklist":tasklist, 
        "agenda_form":form,
        "task_full_form":task_form,
        'format':DATEFORMAT
        })


@login_required(login_url='login_pg')
def time_tracking(request):
    formfile = file_form(request.POST or None)
    formfile.is_valid()

    form = time_filter_form(request.POST or None)
    form.is_valid()
    
    global DICFILTER

    if request.method == "POST":
        if request.POST.get('tracking_sta') == 't': # this is for stop buttom
            period_id = request.POST.get('period_id')
            start_time = work_periods.objects.raw('SELECT apptime_work_periods.id, apptime_work_periods.start_time FROM apptime_work_periods WHERE apptime_work_periods.id = %s', [period_id])
            finish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            complete_period(period_id, request.user.id, start_time[0].start_time.strftime("%Y-%m-%d %H:%M:%S"), finish_time)

        elif request.POST.get('track_filter') == 't': # this is to filter task history
            time = form.cleaned_data.get("time")
            task_name = request.POST["task"]
            label = request.POST["label"]
            assigned_date = form.cleaned_data.get("assigned")
            creation_date = form.cleaned_data.get("created")
            completed = form.cleaned_data.get("completed")
            start = form.cleaned_data.get("start")
            final = form.cleaned_data.get("final")
            userobj = User.objects.get(id=request.user.id)

            # choosing which filters to apply and making timezone conversions.
            format='%Y-%m-%d %H:%M'
            filter_kwargs = {}
            dictionary = {'start_time__gte':start,'finish_time__lte': final,'task_id__comple_sta': completed,'task_id__user_id': userobj, 'task_id__task_name__icontains': task_name, 'task_id__label__icontains': label, 'task_id__assigned_date__icontains': assigned_date, 'task_id__creation_date__icontains': creation_date}
            for key, value in dictionary.items():
                if value:
                    if key in ['finish_time__lte','start_time__gte','task_id__creation_date__contains']:
                        filter_kwargs[key] = str(value.astimezone(pytz.timezone('UTC')).strftime(format))
                    else:
                        filter_kwargs[key] = value
            
            elements = work_periods.objects.select_related('task_id').filter(**filter_kwargs).order_by('-start_time').values('id', 'task_id__task_name', 'task_id__label', 'start_time', 'finish_time', 'total_time', 'task_id__tracking_sta')
            if time:
                time = str(time.astimezone(pytz.timezone('UTC')).strftime(format))
                temp_finish = elements
                temp_start = elements

                temp_finish = temp_finish.filter(finish_time__gte=time)
                temp_start = temp_start.filter(start_time__lte=time)
                elements = temp_finish.intersection(temp_start)

            DICFILTER = elements
            total = DICFILTER.aggregate(total=Sum('total_time'))

            return render(request, "apptime/time_tracking.html", context={
                "elements":elements, 
                "time_filter_form":form, 
                "file_form":formfile, 
                'format':DATETIMEFORMAT,
                'total':total['total']
                })

        elif request.POST.get("order") == 't':

            order = {'o_task': request.POST.get("o_task"),'o_label': request.POST.get("o_label"),'o_start': request.POST.get("o_start"),'o_time': request.POST.get("o_time")}
            orderparam = ['task_id__task_name', "task_id__label", "start_time", "total_time"]
            count = 0

            for key in order.keys():
                temp = request.POST.get(key)
                if temp == '1' or temp == '0':
                    order[key] = int(temp)
                    tempdic = ordertimetrack(order, key, DICFILTER, orderparam[count])
                    DICFILTER = tempdic['dicquery']
                    order = tempdic['orderdic']

                    break
                count += 1

            total = DICFILTER.aggregate(total=Sum('total_time'))

            return render(request=request, template_name="apptime/time_tracking.html", context={
                "elements":DICFILTER, 
                "time_filter_form":form, 
                "file_form":formfile, 
                "order":order, 
                "format":DATETIMEFORMAT,
                'total':total['total']
                })

        # CVS file download
        elif request.POST.get('csvdownload') == 't':
            # Define Django project base directory
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Name file
            filename = request.POST.get('filename')   
            if not filename:
                filename = datetime.now().strftime("report_%Y%m%d")
            filename = filename + '.csv'

            # Define the full file path
            filepath = BASE_DIR + '/apptime/files/' + filename

            # create file
            format = '%Y-%m-%d %-I:%M %p'
            with open(filepath, "a", newline='\n') as f:
                f.write("Task, Label, Start, Finish, Time(hr)\n")
                for row in DICFILTER:
                    f.write(row['task_id__task_name'] + ',' + row['task_id__label'] + ',' + timezone.localtime(row['start_time']).strftime(format) + ',' + timezone.localtime(row['finish_time']).strftime(format) + ',' + str(row['total_time']) + '\n')
                f.close()

            # Open the file for reading content
            path = open(filepath, 'rb')

            # Set the mime type
            mime_type, _ = mimetypes.guess_type(filepath)

            # Set the return value of the HttpResponse
            response = HttpResponse(path, content_type=mime_type)

            # Set the HTTP header for sending to browser
            response['Content-Disposition'] = "attachment; filename=%s" % filename

            # Deleate file
            os.remove(filepath)

            # Return the response value
            return response

        # PDF file download
        elif request.POST.get('pdfdownload') == 't':
            width, height = letter
            format = '%Y-%m-%d %-I:%M %p'
            response = HttpResponse(content_type='application/pdf')

            filename = request.POST.get('filename')   
            if not filename:
                filename = datetime.now().strftime("report_%Y%m%d")
            filename = filename + '.pdf'
            stylesheet=getSampleStyleSheet()

            # Create the PDF object with a letter size
            p = canvas.Canvas(response, pagesize=letter)

            # bolding headings
            P0 = Paragraph('''<b>Task</b>''',
                            stylesheet["BodyText"])
            P1 = Paragraph('''<b>Label</b>''',
                            stylesheet["BodyText"])
            P2 = Paragraph('''<b>Start</b>''',
                            stylesheet["BodyText"])
            P3 = Paragraph('''<b>Finish</b>''',
                            stylesheet["BodyText"])
            P4 = Paragraph('''<b>Time</b>''',
                            stylesheet["BodyText"])

            data = [
                [P0, P1, P2, P3, P4]
            ]

            datarow = []

            # Append query data to data dic
            for row in DICFILTER:
                for key, value in row.items():
                    if key in ['task_id__task_name', 'task_id__label', 'start_time', 'finish_time', 'total_time']:
                        if key in ['start_time', 'finish_time']:
                            temp = timezone.localtime(row[key]).strftime(format)
                            datarow.append(temp)
                        else:
                            datarow.append(value)

                data.append(datarow)
                datarow = []

            # get the total number of hrs
            total = DICFILTER.aggregate(total=Sum('total_time'))

            # bold total
            P5 = Paragraph(f'''<b>{total['total']}</b>''',
                stylesheet["BodyText"])

            # add the last line to the **char
            datarow = ['','','','',P5]
            data.append(datarow)
            datarow = []           

            # get the number of rows
            nrows = len(data)
            rpp = 40

            # divide the number rows by the number of rows per page.
            npages = math.ceil(nrows / rpp)
            
            # create each page of the PDF
            for i in range(npages):
                # create table obj
                f = Table(data[0+(rpp*i):rpp+(rpp*i)], [(width-(inch))*(141/385), (width-(inch))/7,(width-(inch))/5,(width-(inch))/5,(width-(inch))/11])
                f.setStyle(TableStyle([
                        ('ROWBACKGROUNDS', (0, 0), (-1, -1), (0xeaece5, None)),
                        ('TEXTCOLOR',(0,0),(-1,-1), (0x2f2f2f))
                        ]))

                w, h = f.wrapOn(p, width, height)

                # if the table is bigger than the paper size, raise an error
                if w >= width:
                    raise ValueError

                f.drawOn(p, inch/2, height-h-inch/2)
                
                # Close page
                p.showPage()

            p.save()

            return response

    userobj = User.objects.get(id=request.user.id)
    elements = work_periods.objects.select_related('task_id').filter(task_id__user_id=userobj).order_by('-start_time').values('id', 'task_id__task_name', 'task_id__label', 'start_time', 'finish_time', 'total_time', 'task_id__tracking_sta')
    DICFILTER = elements
    total = work_periods.objects.select_related('task_id').filter(task_id__user_id=userobj).aggregate(total=Sum('total_time'))

    return render(request=request, template_name="apptime/time_tracking.html", context={
        "elements":DICFILTER, 
        "time_filter_form":form, 
        "file_form":formfile,
        'format':DATETIMEFORMAT,
        "total":total['total']
        })


def task_autocomplete(request):
    if request.GET.get('q'):
        q = request.GET['q']
        data = tasks.objects.filter(user_id__id=request.user.id, task_name__contains=q).values_list('task_name',flat=True).distinct()[:5]
        json = list(data)

        return JsonResponse(json, safe=False)
        
    return HttpResponse("Incorrect request")


def label_autocomplete(request):
    if request.GET.get('l'):
        q = request.GET.get('l')
        data = tasks.objects.filter(user_id__id=request.user.id, label__contains=q).values_list('label',flat=True).distinct()[:5]

        json = list(data)

        return JsonResponse(json, safe=False)
    return HttpResponse("Incorrect request")


@login_required(login_url='login_pg')
def start_task(request):
    if request.method == "POST":
        # get form
        form = start_task_form(request.POST)

        # Get task, label, start time, finish time...
        task = request.POST["task"]
        label = request.POST["label"]
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        create_incomplete_period(request.user.id, None, task, label, start_time)

        # redirect user to time tracking page
        return HttpResponseRedirect("time_tracking")

    form = start_task_form()
    return render(request=request, template_name="apptime/start_task.html", context={"start_form":form})


@login_required(login_url='login_pg')
def log_time(request):
    if request.method == "POST":
        # Get form
        form = log_prev_time_form(request.POST)
        if form.is_valid():
            # Get task, label, start time, finish time...
            task = request.POST["task"]
            label = request.POST["label"]
            start_time = form.cleaned_data.get("start_time")
            finish_time = form.cleaned_data.get("finish_time")

            # Adding the proper filters to the query
            filter_kwargs = {}
            dictionary = {'user_id':request.user.id,'task_name': task, 'label': label}
            for key, value in dictionary.items():
                if value:
                    filter_kwargs[key] = value

            taskquery = tasks.objects.filter(**filter_kwargs)

            # debugging purposes
            """
            print('START:', start_time, type(start_time))
            print('FINISH:', finish_time, type(finish_time))
            """

            # If the task does not exists
            if not taskquery:
                # get user's object
                userobj = User.objects.get(id=request.user.id)

                # Create task / insert it in the tasks table
                task_to_insert = tasks(user_id = userobj, task_name = task, label = label)
                task_to_insert.save()

                # get task
                taskquery = tasks.objects.filter(**filter_kwargs)

            # calculate the total time in hours
            total_time = finish_time - start_time  
            total_time = total_time.total_seconds() / 3600

            # insert time period into proper table
            time_period_insert = work_periods(task_id = taskquery[0], start_time = start_time, finish_time = finish_time, total_time = total_time)
            time_period_insert.save()

        # redirect user to time tracking page
        return HttpResponseRedirect("time_tracking")
    form = log_prev_time_form()
    return render(request=request, template_name="apptime/log_time.html", context={"log_form":form})


@login_required(login_url='login_pg')
def edit_task(request, task_id):
    storage = None

    if request.method == "POST":
        # Get form
        form = task_full_form(request.POST)

        if form.is_valid():
            task_name = form.cleaned_data.get("task")
            label = form.cleaned_data.get("label")
            assigned_date = form.cleaned_data.get("assigned")
            description = form.cleaned_data.get("description")

            filter_kwargs = {}
            dictionary = {'task_name': task_name, 'label': label, 'assigned_date': assigned_date, 'description': description}
            for key, value in dictionary.items():
                if value:
                    filter_kwargs[key] = value
            
            # Update task
            tasks.objects.filter(id=task_id, user_id=request.user).update(**filter_kwargs)
            
            messages.success(request, "The task was updated.")
            storage = get_messages(request)
            return HttpResponseRedirect(reverse('agenda'))

        messages.error(request, "Could not update task")
        storage = get_messages(request)
        return HttpResponseRedirect(request.path)
    else:
        form = task_full_form()
        return render(request, template_name="apptime/taskform.html", context={"task_full_form":form, "messages":storage})


@login_required(login_url='login_pg')
def taskinfo(request, task_id):
    if request.method == "POST":
        if request.POST.get('delete') == 't':
            # delete task
            task = tasks.objects.get(id=task_id)
            task.delete()

            # redirect to agenda page
            return HttpResponseRedirect("agenda")
        elif request.POST.get('edit') == 't':
            # redirect to edit task path
            return HttpResponseRedirect("agenda")

    # Get task object
    task = tasks.objects.get(id=task_id)

    # Get the total time for the task
    with connection.cursor() as cursor:
        cursor.execute("""SELECT SUM(total_time) AS task_total FROM apptime_work_periods 
                            JOIN apptime_tasks ON apptime_work_periods.task_id_id = apptime_tasks.id
                            WHERE task_id_id = %s  AND user_id_id = %s
                            GROUP BY apptime_work_periods.task_id_id""", [task_id, request.user.id])
        total = cursor.fetchall()

    # conver total to decimal
    if total:
        total = list(total[0])[0]

    # Get the work periods of the requested task
    elements = work_periods.objects.raw("""SELECT apptime_work_periods.id, apptime_work_periods.start_time AS start, apptime_work_periods.finish_time AS finish, apptime_work_periods.total_time AS total 
                                                FROM apptime_work_periods
                                                JOIN apptime_tasks ON apptime_work_periods.task_id_id = apptime_tasks.id
                                                WHERE task_id_id = %s AND user_id_id = %s""", [task_id, request.user.id])

    return render(request, "apptime/taskinfo.html", {
        "task": task,
        "task_total": total,
        "elements": elements
    })

"""
functions used above:
"""
# returns a dictionary with keys (sunday to saturday) and its dates as strings given the date of sunday (in datetime type) and a string format (ex: "%Y-%m-%d").
def calc_week(now, format):
    # Create a dictionary with the dates that need to be displayed starting from Sunday
    datesdic = {}

    # fill dictionary
    for i in ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']:
        datesdic[i] = now.date()
        if format:
            datesdic[i] = datesdic[i].strftime(format)
        now = now + timedelta(days=1)

    return datesdic


# returns a raw() dictionary with the assigned dates converted to the specified format. Datesdic as returned by calc_week()
def find_tasks_for_week(user_id, datesdic, format):

    tasklist = tasks.objects.filter(user_id=user_id, assigned_date__in=list(datesdic.values())).annotate(task=F('task_name'), assigned=F('assigned_date'), tracking=F('tracking_sta'), complete=F('comple_sta'))

    # Convert the assigned datetimes into strings so that they can be compared with the datesdic elements.
    if format:
        for task in tasklist:
            task.assigned = task.assigned.strftime(format)

    return tasklist


# checks if a given task already exists. If so, creates an associated, incomplete work period. If not, creates the task and the incomplete work period.
# parameters: logged user's id, task's id (=None if does not exist), task's name, task's label (=None if does not exist), work_period's start time.
def create_incomplete_period(user_id, task_id, name, label, start_time):

    # get query, if it exist, with the provided information.
    filter_kwargs = {}
    dictionary = {'task_name': name, 'label': label, 'id': task_id, 'user_id':user_id, 'comple_sta':'f'}
    for key, value in dictionary.items():
        if value:
            filter_kwargs[key] = value

    taskquery = tasks.objects.filter(**filter_kwargs)

    # If the task does not exists
    if not taskquery:
        # get user's object
        userobj = User.objects.get(id=user_id)

        # Create task / insert it in the tasks table
        task_to_insert = tasks(user_id = userobj, task_name = name, label = label, tracking_sta = True)
        task_to_insert.save()

         # get task's id
        taskquery = tasks.objects.filter(user_id = user_id, task_name=name, label = label, tracking_sta = True, comple_sta='f')
    # UPDATE existing task
    else:
        with connection.cursor() as cursor:
            cursor.execute("""UPDATE apptime_tasks
                                SET tracking_sta = 't'
                                WHERE apptime_tasks.user_id_id = %s AND apptime_tasks.id = %s
                                """, (user_id, taskquery[0].id))

    # make a incomplete time period
    time_period_insert = work_periods(task_id = taskquery[0], start_time = start_time, finish_time = None, total_time = None)
    time_period_insert.save()

    return 0


# completes a period created by create_incomplete_period(). Updates the empty fields for the work periods table and the tracking status of the tasks table.
# parameters: the work period's id (int), logged user's id (int), the starting time of the period (str), the finishing time of the period (str).
def complete_period(period_id, user_id, start_time, finish_time):
    # calculate the total time in hours
    total_time = datetime.fromisoformat(finish_time) - datetime.fromisoformat(start_time)   
    total_time = total_time.total_seconds() / 3600

    # Update the time periods table
    query = work_periods.objects.select_related('task_id').get(task_id__user_id = user_id, id = period_id)
    query.finish_time = finish_time
    query.total_time = total_time
    query.save()

    # Update the tasks table so that the tracking status is false.
    with connection.cursor() as cursor:
        cursor.execute("""UPDATE apptime_tasks
                            SET tracking_sta = 'f'
                            WHERE apptime_tasks.user_id_id = %s AND apptime_tasks.id = (
                                SELECT apptime_work_periods.task_id_id
                                FROM apptime_work_periods
                                WHERE apptime_work_periods.id = %s
                            )""", (user_id, period_id))


# Takes the status of an ordering by filter in the time tracking page (wherther increasing or decreasing) and switches the status.
# Then it applies the proper ordering filter to the query displayed.
# Parameters: 
    # orderdic is used in the time tracking pages to decide the status of a filter. It is a dictionary with 0's, 1's, or None objects. 
    # the key is the orderdic key that contains the status of the filter in question.
    # the dicquery is the query that will be re-ordered.
    # the field is the name of the column that will be re-ordered.
# Returns a dictionary with the updated dicquery and the updated orderdic
def ordertimetrack(orderdic, key, dicquery, field):
    if orderdic[key] == 1:
        orderdic[key] = 0

        str = "-"+field
        dicquery = dicquery.order_by(str)

    else:
        orderdic[key] = 1
        dicquery = dicquery.order_by(field)

    returndic = {"dicquery":dicquery, "orderdic":orderdic}

    return returndic