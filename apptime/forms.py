from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from apptime.models import profile
import pytz
from django.contrib.flatpages.models import FlatPage
from tinymce.widgets import TinyMCE
from tinymce import models as tinymce_models

# Global variables
TIMEZONES = tuple(zip(pytz.common_timezones, pytz.common_timezones))

completedchoices = (
    ("t", "yes"),
    ("f", "no")
	)

# Define widgets

class dateinput(forms.DateInput):
	input_type = 'date'


class datetimeinput(forms.DateInput):
	input_type = 'datetime-local'


# Create your forms here.

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

	def save(self, commit=True):
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']

		if commit:
			user.save()
		return user

class ChangePass(PasswordChangeForm):
	def __init__(self, *args, **kwargs):
		super(ChangePass, self).__init__(*args, **kwargs)
		self.fields['old_password'].widget.attrs.update({'autofocus': False})

class timezoneform(forms.Form):
	timezone = forms.CharField(label='timezone', widget=forms.Select(choices=TIMEZONES), required=False)


class loginform(forms.Form):
	username = forms.CharField(label='Username', max_length=100)
	password = forms.CharField(widget=forms.PasswordInput(), label='Password', max_length=100)


class start_task_form(forms.Form):
	task = forms.CharField(label='Task', max_length=100)
	label = forms.CharField(label='Label', max_length=100, required=False)


class log_prev_time_form(forms.Form):
	task = forms.CharField(label='Task', max_length=100)
	label = forms.CharField(label='Label', max_length=100, required=False)
	start_time = forms.DateTimeField(label='Start time', input_formats=['%Y-%m-%d %H:%M'], widget=datetimeinput)
	finish_time = forms.DateTimeField(label='Finish time', input_formats=['%Y-%m-%d %H:%M'], widget=datetimeinput)


class agenda_form(forms.Form):
	agendadate = forms.DateTimeField(label='', input_formats=['%Y-%m-%d'], widget=dateinput)


class task_full_form(forms.Form):
	task = forms.CharField(label='', max_length=100, required=False)
	label = forms.CharField(label='', max_length=100, required=False)
	assigned = forms.DateTimeField(label='Due', input_formats=['%Y-%m-%d'], widget=dateinput, required=False)
	description = forms.CharField(widget=TinyMCE(attrs={'id':'textarea-full', 'height':100}), required=False)


class time_filter_form(forms.Form):
	time = forms.DateTimeField(label='Time', input_formats=['%Y-%m-%d %H:%M'], required=False, widget=datetimeinput)
	task = forms.CharField(label='Task', max_length=100, required=False, widget=forms.TextInput(
        attrs={
            'class': 'basicAutoComplete1',
			'autocomplete':"off"
        }))
	label = forms.CharField(label='Label', max_length=100, required=False, widget=forms.TextInput(
		attrs={
            'class': 'basicAutoComplete',
			'autocomplete':"off"
        }))
	assigned = forms.DateTimeField(label='Due Date', input_formats=['%Y-%m-%d'], required=False, widget=dateinput)
	created = forms.DateTimeField(label='Creation', input_formats=['%Y-%m-%d'], widget=dateinput, required=False)
	start = forms.DateTimeField(label='', input_formats=['%Y-%m-%d %H:%M'], widget=datetimeinput, required=False)
	final = forms.DateTimeField(label='', input_formats=['%Y-%m-%d %H:%M'], widget=datetimeinput, required=False)
	completed = forms.ChoiceField(label='Completed?', widget=forms.RadioSelect, choices=completedchoices, required=False)


class file_form(forms.Form):
	filename = forms.CharField(label='filename', max_length=100, required=False)


class account_form(forms.Form):
	username = forms.CharField(label='Username', max_length=100, required=False)
	email = forms.EmailField(label='Email', max_length=100, required=False)
	timezone = forms.TypedChoiceField(label='Timezone', choices=TIMEZONES, required=False)


class text_editor_form(forms.Form):
	editor = forms.CharField(widget=TinyMCE(attrs={'id':'textarea-full', 'cols': 80, 'rows': 30, 'height':1000}), required=False)