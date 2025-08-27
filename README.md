# Course Finder Website

This is a Django website for finding university courses.

Create a new .env file with the appropriate password:

EMAIL_HOST_USER=unimatch.nea@gmail.com
EMAIL_HOST_PASSWORD=PASSWORD HERE

## How to run this project

First you need Python and PostgreSQL installed on your Mac.

Install PostgreSQL if you don't have it:
```
brew install postgresql
```

### Setting up the project

Clone the project and go into the folder:
```
git clone https://github.com/zainab-gilani/Website.git
cd Website
```

Create a virtual environment:
```
python3 -m venv .venv
source .venv/bin/activate
```

Install the required packages:
```
pip install --upgrade pip
pip install -r requirements/dev.txt
pip install python-dotenv certifi
```

### Database setup

Start PostgreSQL:
```
brew services start postgresql
```

Create the database user and database:
```
createuser -s postgres
createdb -U postgres postgres
```

Create and run migrations for the database:
```
python manage.py makemigrations
python manage.py migrate
```

If you encounter a "relation already exists" error during migration, 
it means the database tables exist but Django doesn't know about them. 
Fix this by marking the initial migration as fake argument applied:
```
python manage.py migrate coursefinder 001_initial --fake
python manage.py migrate
```

### Create admin user

Create an admin account:
```
python manage.py createsuperuser --username admin --email admin@example.com --noinput
python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='admin'); u.set_password('123'); u.save()"
```

### Run the website

Start the server:
```
python manage.py runserver
```

The website will be at http://127.0.0.1:8000/
The admin page is at http://127.0.0.1:8000/admin/ (login with admin/123)