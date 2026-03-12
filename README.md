# EventHub — Event Registration System

A production-ready Django application for discovering, creating, and registering for events.

## Features

- **User Authentication** — Sign up, login, logout, profile management
- **Event Management** — Full CRUD for admin/organizers with image uploads
- **Registration System** — Register/cancel with capacity limits & duplicate prevention
- **Search & Filter** — Search by title/location, upcoming events, pagination
- **Responsive UI** — Bootstrap 5, mobile-friendly, modern card layout
- **Production Ready** — WhiteNoise, PostgreSQL support, security hardening

---

## Quick Start

### 1. Clone & Create Virtual Environment

```bash
git clone https://github.com/veereshawaralli/EVENT-REGISTRATION.git
cd event_registration
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables (optional for dev)

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Project Structure

```
event_registration/
├── config/             # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/           # User auth & profiles
├── events/             # Event CRUD & listing
├── registrations/      # Registration logic & dashboard
├── templates/          # HTML templates
├── static/             # CSS, JS
├── media/              # Uploaded images (dev)
├── manage.py
├── requirements.txt
├── Procfile
└── runtime.txt
```

---

## Deployment

### Environment Variables (Production)

| Variable             | Description                          |
|----------------------|--------------------------------------|
| `SECRET_KEY`         | Django secret key                    |
| `DEBUG`              | Set to `False`                       |
| `ALLOWED_HOSTS`      | Comma-separated host list            |
| `DATABASE_URL`       | PostgreSQL connection string         |
| `SECURE_SSL_REDIRECT`| Set to `True` for HTTPS redirect     |

### Render / Railway / Heroku

1. Push your repository to GitHub.
2. Connect the repo to your platform.
3. Set the above environment variables.
4. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
5. Start command: `gunicorn config.wsgi`

### VPS (Gunicorn + Nginx)

```bash
# Install
pip install -r requirements.txt

# Collect static
python manage.py collectstatic --noinput

# Migrate
python manage.py migrate

# Run with Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

Configure Nginx to proxy to `127.0.0.1:8000` and serve `/static/` from the `staticfiles/` directory.

---

## Running Tests

```bash
python manage.py test
```

---

## Tech Stack

- **Backend**: Django 5.1, Python 3.12
- **Frontend**: Bootstrap 5, Bootstrap Icons, Inter font
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Static files**: WhiteNoise
- **Server**: Gunicorn

---

## License

MIT
