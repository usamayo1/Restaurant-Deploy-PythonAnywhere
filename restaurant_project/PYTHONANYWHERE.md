# PythonAnywhere Deployment Guide

This project can run on PythonAnywhere's free plan using SQLite.

## What to upload

Push these files to GitHub:

- project source code
- `requirements.txt`
- `manage.py`
- `templates/`
- `static/`

Do not upload:

- `venv/` or `.venv/`
- `__pycache__/`
- local secrets

## Free-plan notes

- Free PythonAnywhere accounts can host one web app.
- Free accounts use a `yourusername.pythonanywhere.com` domain.
- Free accounts are fine for a student/demo project.
- Keep `DATABASE_URL` empty so Django uses SQLite.

## 1. Create the PythonAnywhere account

Create a free account at:

- `https://www.pythonanywhere.com/`

## 2. Open a Bash console

In PythonAnywhere, open a Bash console and run:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If PythonAnywhere shows a different Python version in the Web tab, use that same version for the virtual environment.

## 3. Create the web app

In the `Web` tab:

1. Click `Add a new web app`.
2. Choose your free domain like `yourusername.pythonanywhere.com`.
3. Choose `Manual configuration`.
4. Pick the same Python version you used for the virtual environment.

## 4. Configure the WSGI file

Open the generated WSGI file from the `Web` tab and replace its contents with this template.

Update `yourusername` and `YOUR_REPO_NAME` first:

```python
import os
import sys

path = "/home/yourusername/YOUR_REPO_NAME"
if path not in sys.path:
    sys.path.append(path)

os.environ["DJANGO_SETTINGS_MODULE"] = "restaurant_project.settings"
os.environ["DJANGO_SECRET_KEY"] = "replace-this-with-a-long-random-value"
os.environ["DJANGO_DEBUG"] = "false"
os.environ["DJANGO_ALLOWED_HOSTS"] = "yourusername.pythonanywhere.com"
os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"] = "https://yourusername.pythonanywhere.com"
os.environ["PYTHONANYWHERE_DOMAIN"] = "yourusername.pythonanywhere.com"

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

If you later use a paid account with Postgres, you can also set:

```python
os.environ["DATABASE_URL"] = "your-postgres-connection-string"
```

## 5. Run migrations and collect static files

Back in the Bash console:

```bash
cd ~/YOUR_REPO_NAME
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 6. Configure static and media files

In the `Web` tab, add these mappings:

- URL: `/static/`
- Directory: `/home/yourusername/YOUR_REPO_NAME/staticfiles`

- URL: `/media/`
- Directory: `/home/yourusername/YOUR_REPO_NAME/media`

## 7. Set the virtualenv path

In the `Web` tab, set the virtualenv path to:

```text
/home/yourusername/YOUR_REPO_NAME/.venv
```

## 8. Reload the web app

Click `Reload` on the `Web` tab.

Then test:

- `/`
- `/health/`
- `/admin/`

## Google login note

If you use Google login, update your Google OAuth app with this callback URL:

```text
https://yourusername.pythonanywhere.com/accounts/google/login/callback/
```

## Troubleshooting

If the site does not load:

- check the `Error log` in the PythonAnywhere `Web` tab
- confirm the virtualenv path is correct
- confirm `DJANGO_DEBUG` is `false`
- confirm `DJANGO_ALLOWED_HOSTS` includes your PythonAnywhere domain
- run `python manage.py collectstatic --noinput` again after static file changes
