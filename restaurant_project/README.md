# Restaurant Project (Django)

## Stack
- Django 6
- django-allauth (Google auth)
- SQLite (default)

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Apply migrations:
   - `python manage.py migrate`
4. Run server:
   - `python manage.py runserver`

## Environment Variables
Use these for secure/prod deployment:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (`true`/`false`)
- `DJANGO_ALLOWED_HOSTS` (comma-separated)
- `DJANGO_CSRF_TRUSTED_ORIGINS` (comma-separated)
- `DATABASE_URL` (Render Postgres connection string for production)
- `DJANGO_TIME_ZONE` (default: `Asia/Karachi`)
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SECURE_HSTS_SECONDS`

You can start from `.env.example`.

## Render Deployment
- The repo includes `render.yaml` for a free Render web service and free Render Postgres database.
- The repo includes `build.sh`, which installs dependencies, runs `collectstatic`, and applies migrations.
- Static files are served with WhiteNoise in production.
- Local development still falls back to SQLite when `DATABASE_URL` is not set.
- Do not commit `venv/`, `.venv/`, or local secrets.
- Do not rely on local `media/` uploads in Render free hosting, because filesystem changes are not persistent across redeploys/restarts.

## PythonAnywhere Deployment
- This project also works on PythonAnywhere with SQLite on the free plan.
- Set `PYTHONANYWHERE_DOMAIN` to your PythonAnywhere hostname, for example `yourusername.pythonanywhere.com`.
- Keep `DATABASE_URL` empty on the free plan so the app uses SQLite.
- Run `python manage.py collectstatic` after uploading the code.
- Configure static files in PythonAnywhere's Web tab to serve `/static/` from the project's `staticfiles` directory.
- A full step-by-step guide is in `PYTHONANYWHERE.md`.

## Tests
Run:
- `python manage.py test`

Core tests cover:
- Cart mutation endpoints and method restrictions
- Order placement validations
- Order tracking permissions/visibility
- Order cancellation authorization
- Automatic status progression

## Notes
- Checkout UI is integrated in `cart.html`; `/checkout/` redirects to `/cart/`.
- Mutating cart/order endpoints are POST-only.
- Health endpoint is available at `/health/`.
