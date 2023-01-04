# Time Management App

This is a Django application that simulates an agenda with time-tracking capabilities. The application provides an agenda, a calendar, and a time tracking page. You can create to-do lists for every day and track the time you worked in each task.

## Usage
* Download a zip at https://github.com/MariaJCU/time_management
  * unzip time_management-master.zip
* Create a virtual environment. If you are in ubuntu:
  * virtualenv enviroment_name
  * source environment_name/bin/activate
* Go to the application directory
  * cd time_management-master
* Install the application dependencies
  * pip install -r requirements.txt
* Create PostgreSQL Database.
  * psql postgres
  * CREATE DATABASE time_db;
  * \connect time_db
* Create an .env file in the time_management-master directory. You may use the .env.example as reference.
* Run the application
  * python manage.py makemigrations
  * python manage.py migrate
  * python manage.py runserver
* Go to “register” and create your account

## Credits
The following libraries and projects were used for this repository:
* https://getbootstrap.com/
* https://www.djangoproject.com/
* https://www.tiny.cloud
* https://www.reportlab.com/

