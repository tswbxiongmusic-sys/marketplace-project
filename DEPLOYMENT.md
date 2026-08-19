# Production deployment checklist

## Before deployment

1. Create a managed PostgreSQL database. Enable provider-managed daily backups and point-in-time recovery if it is available. On Render, copy its **Internal Database URL** to `DATABASE_URL`; do not expose that value in source control.
2. Copy `.env.example` to the hosting platform's **secret environment-variable** settings. Never upload `.env` or commit real secrets.
3. Generate a secret key with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` and use it only once in production.
4. Set the real domain in `ALLOWED_HOSTS` and its HTTPS URL in `CSRF_TRUSTED_ORIGINS`. Leave `SECURE_HSTS_PRELOAD=True` only when the root domain and every active subdomain support HTTPS.
5. Create a media storage bucket for uploads — either an R2/S3 bucket (requires a payment method on file, though R2 itself stays free under 10GB) or a Cloudinary account (free tier, no payment method required). Configure private credentials in the host, enable bucket encryption if using R2/S3, and use the media domain only after it has HTTPS.
6. Configure an SMTP provider and verify `DEFAULT_FROM_EMAIL` with that provider.
7. If social sign-in is enabled, create Google and/or Facebook OAuth applications, add the exact HTTPS callback URLs from `SOCIAL_LOGIN_SETUP.md`, and set their credentials as secret environment variables.

## Deploy

Install dependencies, then run the release command and web command from `Procfile`:

```bash
pip install -r requirements.txt
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --access-logfile - --error-logfile -
```

Configure the platform health-check path as `/health/`. It returns 200 only when Django can connect to PostgreSQL.

## Domain and HTTPS

Point the domain DNS record at the selected host, attach the domain in the host dashboard, and enable the platform's managed TLS certificate. Do not set `DEBUG=True` in production. HTTPS is required because secure cookies and redirects are enabled.

## Backup and recovery

Use the database provider's automated backups as the primary backup. Also run `bash scripts/backup_postgres.sh` on a protected schedule, then copy the generated `backups/*.dump` to encrypted off-site storage. Test restoration in a separate database before relying on a backup.

## Payment

The application currently accepts cash on delivery and bank/QR receipts. An automatic card/payment gateway needs a merchant account, webhook secret, and a provider chosen by the business owner; it should not be enabled with placeholder credentials.

## Social login

Follow `SOCIAL_LOGIN_SETUP.md` after the production domain is live. Do not put OAuth client secrets in source control, browser JavaScript, or the Django admin. The site hides a provider until its ID and secret are present in environment variables.
