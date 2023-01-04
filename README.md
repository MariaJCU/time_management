# Time Management App

This is a Django application that simulates an agenda with time-tracking capabilities. The application provides an agenda, a calendar, and a time tracking page. You can create to-do lists for every day and track the time you worked in each task.

## Usage
* Download a zip at https://github.com/MariaJCU/time_management
  * Unzip time_management-master.zip
* Create a virtual environment. If you are in ubuntu:
  * Virtualenv enviroment_name
  * Source environment_name/bin/activate
* Go to the application directory
  * Cd time_management-master
* Install the application dependencies
  * Pip install -r requirements.txt
* Create PostgreSQL Database.
  * Psql postgres
  * CREATE DATABASE time_db;
  * \connect time_db
* Create an .env file in the time_management-master directory. You may use the .env.example as reference.
* Run the application
  * Python manage.py makemigrations
  * Python manage.py migrate
  * Python manage.py runserver
* Go to “register” and create your account

## Credits
The following libraries and projects were used for this repository:
* https://getbootstrap.com/
* https://www.djangoproject.com/
* https://www.tiny.cloud
* https://www.reportlab.com/

