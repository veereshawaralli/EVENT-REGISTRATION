# EventHub — Event Registration System

A production-ready Django application for discovering, creating, and registering for events.

## 🎯 Project Mission
EventHub aims to bridge the gap between event organizers and attendees by providing a seamless, automated, and highly customizable platform. Whether you are hosting a local workshop or a global conference, EventHub provides the tools to manage registrations, payments, and professional certifications with ease.

## ✨ Key Features

- **📜 Interactive Certificate Builder** — Create stunning, coordinate-based PDF certificates with a drag-and-drop WYSIWYG editor.
- **🤖 AI Event Content Generator** — Instantly generate professional event titles, descriptions, and tags using Gemini AI.
- **🔍 QR Ticket Verification** — Built-in HTML5 QR scanner for organizers to verify attendee tickets in real-time.
- **⏳ Smart Waitlist System** — Automatically manage interest for sold-out events with an intelligent waitlisting flow.
- **📈 Organizer Dashboard** — Real-time revenue analytics, registration graphs (Chart.js), and one-click CSV attendee exports.
- **📝 Custom Registration Forms** — Create unique questions per event (e.g., T-shirt size, meal preference) with dynamic form validation.
- **📧 Automated Notifications** — Rich HTML emails for confirmations, waitlist updates, and 24h event reminders.
- **💳 Payment Integration** — Secure **Razorpay** integration for online payments and 'Pay at Venue' support.
- **🤖 AI Platform Assistant** — Conversational chatbot to help users find events and navigate the platform.
- **🛡️ Policy Compliant** — Ready-to-use templates for About, Contact, Privacy, Terms, and Refund policies (Razorpay verified).

---

## 👥 User Roles

### **Organizer**
- Create and manage events with custom categories and tags.
- Build custom registration forms for each event.
- Design unique certificates using the Interactive Builder.
- View real-time analytics and export attendee lists.

### **Attendee**
- Browse and search for events using dynamic filters.
- Register for events and make secure payments.
- Access a personal dashboard with QR-coded tickets.
- Download certificates and leave reviews for attended events.

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
├── config/             # Django project settings (settings, URLs, WSGI/ASGI)
├── accounts/           # User authentication & profile management
├── events/             # Event management & Interactive Certificate Builder
├── registrations/      # Registration logic & QR code ticket generation
├── api/                # REST API endpoints for external integrations
├── chatbot/            # AI-powered event assistant & support
├── reviews/            # Attendee feedback & star rating system
├── comments/           # Real-time event discussions & social interaction
├── static/             # Global assets (CSS, JS, Images)
├── templates/          # HTML templates & email designs
├── media/              # User-uploaded content (Banners, Certificates)
├── manage.py           # Django management script
├── requirements.txt    # Project dependencies
├── Procfile            # Deployment instructions for Render/Heroku
└── render.yaml         # Infrastructure as Code for Render deployment
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

Automate routine tasks using the following commands:

- **Send Reminders**: `python manage.py send_event_reminders` (Sends 24h reminders to attendees).
- **Seed Categories**: `python manage.py seed_categories` (Initializes the platform with standard event categories).
- **Setup Admin**: `python manage.py setup_superuser` (Automated script to create a pre-configured admin account).
- **Test Email**: `python manage.py test_email` (Verifies SMTP/Brevo connection).

---

## Running Tests

```bash
python manage.py test
```

---

## 🎨 How the Certificate Builder Works

The **Interactive Certificate Builder** is designed for pixel-perfect accuracy:
1. **Upload Background**: Organizers upload an A4 Landscape background image.
2. **Drag & Drop Editor**: Using `Interact.js`, elements like "Attendee Name" and "Date" can be positioned anywhere on the canvas.
3. **Coordinate-Based Mapping**: The builder saves coordinates as percentages (`x`, `y`) to ensure responsiveness across different screen sizes.
4. **PDF Generation**: When a certificate is generated, `xhtml2pdf` uses these coordinates to calculate precise `mm` positions on an A4 page, guaranteeing that the final PDF looks exactly like the preview.

---

## 🛠️ Detailed Tech Stack

- **Backend**: Django 5.1 (Python 3.12)
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Frontend**: 
  - **Styling**: Bootstrap 5, Custom CSS3
  - **Interactivity**: Interact.js (for Drag & Drop), Chart.js (for Analytics)
- **Utilities**:
  - **PDF Generation**: xhtml2pdf & ReportLab
  - **Image Processing**: Pillow (PIL)
  - **Ticketing**: Python-QRCode
  - **Payments**: Razorpay SDK
- **Infrastructure**:
  - **Storage**: Cloudinary (Media files)
  - **Deployment**: Render (Web Service + Managed PostgreSQL)
  - **Static Hosting**: WhiteNoise

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL (optional for local, required for production)
- Razorpay Account (for payments)
- Cloudinary Account (for image storage)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/veereshawaralli/EVENT-REGISTRATION.git
   cd EVENT-REGISTRATION
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables**
   Create a `.env` file in the root directory and add:
   ```env
   DEBUG=True
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgres://user:password@localhost:5432/eventhub
   CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
   RAZORPAY_KEY_ID=your_key_id
   RAZORPAY_KEY_SECRET=your_key_secret
   ```

5. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the server**
   ```bash
   python manage.py runserver
   ```

---

## 📡 API Endpoints

The system provides a RESTful API for integration:
- `GET /api/events/` - List all upcoming events.
- `GET /api/events/<id>/` - Detailed information about an event.
- `POST /api/registrations/` - Register for an event (requires authentication).
- `GET /api/user/tickets/` - Retrieve a user's purchased tickets.

---

## 🤖 AI Assistant (Chatbot)
The platform features an AI chatbot built using the Gemini API. It can:
- Recommend events based on user interests.
- Explain event details and registration processes.
- Provide general support for platform navigation.

---

## 🛡️ Security Features
- **CSRF Protection**: All forms are protected against Cross-Site Request Forgery.
- **Secure Payments**: No credit card data is stored on our servers; all transactions are handled securely by Razorpay.
- **Signed QR Codes**: Tickets contain unique, signed identifiers to prevent duplication or fraud.

---

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing
Contributions are welcome! Please follow these steps:
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.
