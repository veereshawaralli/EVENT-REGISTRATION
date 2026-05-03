# EventHub — Event Registration System

A production-ready Django application for discovering, creating, and registering for events.

## ✨ Key Features

- **📜 Interactive Certificate Builder** — Create stunning, coordinate-based PDF certificates with a drag-and-drop WYSIWYG editor.
- **🎫 Professional Ticketing** — Secure QR codes for every registration with a built-in mobile-friendly attendee scanner.
- **📈 Organizer Dashboard** — Real-time revenue analytics, registration graphs (Chart.js), and one-click CSV attendee exports.
- **📝 Custom Registration Forms** — Create unique questions per event (e.g., T-shirt size, meal preference) with dynamic form validation.
- **📧 Rich Notifications** — Automated HTML emails for confirmations, waitlist alerts, and 24h event reminders.
- **💳 Flexible Payments** — Integrated with **Razorpay** for online collections and "Pay at Venue" for offline reservations.
- **💬 Social Engagement** — Event-specific discussion comments, star ratings, and viral social sharing buttons.
- **🛡️ Production Hardened** — Optimized for **Render/Vercel**, including Port 2525 email breakthroughs and secure media storage via Cloudinary.
- **Responsive UI** — Modern, premium design using Bootstrap 5, Bootstrap Icons, and the Inter font.

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
├── accounts/           # User auth & password reset
├── events/             # Event CRUD, categories, tags, custom fields
├── registrations/      # Registration core & QR ticketing
├── reviews/            # Attendee star ratings & feedback
├── comments/           # Real-time event discussions
├── templates/          # HTML templates (Email & UI)
├── static/             # CSS (Vanilla), JS
├── media/              # Uploaded banners (Cloudinary in prod)
├── manage.py
├── requirements.txt
├── Procfile            # Deployment script
└── runtime.txt
```

---

## Deployment

### Environment Variables (Production)

| Variable             | Description                                      |
|----------------------|--------------------------------------------------|
| `SECRET_KEY`         | Django secret key (Required in Prod)             |
| `DEBUG`              | Set to `False` in Prod                           |
| `DATABASE_URL`       | PostgreSQL connection string                      |
| `EMAIL_HOST_USER`    | SMTP username (e.g., Brevo/Gmail)                |
| `EMAIL_HOST_PASSWORD`| SMTP password                                    |
| `CLOUDINARY_URL`     | Cloudinary URL for media storage                 |
| `RAZORPAY_KEY_ID`    | Razorpay Key ID for payments                     |
| `RAZORPAY_KEY_SECRET`| Razorpay Secret Key                              |

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

## 🤖 Management Commands

To send automatic **24-hour event reminders** to all confirmed attendees, set up a cron job (or Render/Heroku Scheduler) to run:

```bash
python manage.py send_event_reminders
```

---

## Running Tests

```bash
python manage.py test
```

---

## Tech Stack

- **Backend**: Django 5.1, Python 3.12
- **Frontend**: Bootstrap 5, Bootstrap Icons, Inter font, Interact.js
- **PDF Generation**: xhtml2pdf, ReportLab
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Static files**: WhiteNoise
- **Server**: Gunicorn

---

## License

MIT
