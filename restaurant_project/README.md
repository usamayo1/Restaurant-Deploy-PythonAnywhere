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
- `DJANGO_TIME_ZONE` (default: `Asia/Karachi`)
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SECURE_HSTS_SECONDS`

You can start from `.env.example`.

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
