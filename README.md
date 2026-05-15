# Elevator Service Manager

A Django web application for an elevator maintenance company. It lets the
company manage its clients, their elevators and the service visits performed on
them, while giving clients a portal to view their equipment, follow service
history, report faults and pay for service online via Stripe.

The app has two kinds of users — **company staff** (technicians/office) and
**clients** (elevator owners) — each with their own dashboard, and a built-in
messaging system so the two sides can communicate (including photo-attached
fault reports routed to whichever technician is on shift that day).

> Originally built in 2021 (Django 3.1) and re-published with full
> documentation and the hardcoded secrets moved out of source control.

## Demo

A short video walkthrough of the application:

[![Watch the demo](https://img.youtube.com/vi/AvQJeknxiAQ/maxresdefault.jpg)](https://www.youtube.com/watch?v=AvQJeknxiAQ)

▶️ <https://www.youtube.com/watch?v=AvQJeknxiAQ>

---

## Features

- **Role-based access** — two user groups, `Company` (technicians/staff) and
  `Client`, each with its own dashboard and permissions.
- **Client management** — company staff can add, update and delete client accounts.
- **Elevator registry** — each elevator (hydraulic or mechanical) is registered
  against a client, with technical details such as motor cauldron, control panel,
  book code, wattage, stations, wire ropes and last KTEO inspection date.
- **Service records** — staff log service visits per elevator (cost, technician,
  receipt code, dates); clients can add a comment to a completed service.
- **Weekly shift schedule** — a rolling weekly roster that records which technician
  is on shift each day; alert messages are auto-routed to "today's" technician.
- **Internal messaging** — `Alert` messages (a client reporting a categorized
  elevator fault, optionally with a photo) and `Simple` messages (free-text,
  broadcastable to all clients or all staff), with reply and read-tracking.
- **Online payments** — clients pay for a service through Stripe Checkout.
- **Search & filtering** — service history and elevator search powered by
  `django-filter`.

## Tech stack

| Layer       | Technology                                        |
|-------------|---------------------------------------------------|
| Framework   | Django 3.1.5                                      |
| Language    | Python 3.9                                        |
| Database    | SQLite 3 (default Django dev DB)                  |
| Auth        | Django auth with a custom `User` model and Groups |
| Filtering   | django-filter 2.4                                 |
| Payments    | Stripe Checkout (`stripe` 2.55)                   |
| Images      | Pillow                                            |
| Frontend    | Django templates, vanilla JS, SCSS/CSS            |
| Config      | python-decouple (`.env` file)                     |

## Repository structure

```
elevator-service-manager/
├── manage.py                 # Django management entry point
├── requirements.txt          # Python dependencies
├── .env.example              # template for required environment variables
├── .gitignore
├── README.md
│
├── webapp/                   # Django project configuration
│   ├── settings.py           # settings (reads secrets from .env)
│   ├── urls.py               # root URL config
│   ├── wsgi.py / asgi.py     # WSGI / ASGI entry points
│   └── __init__.py
│
├── core/                     # the single application — all business logic
│   ├── models.py             # data model: User, week, elevators, service, Message
│   ├── views.py              # all request handlers (function-based views)
│   ├── urls.py               # app URL routes
│   ├── forms.py              # ModelForms + the custom user-creation form
│   ├── filters.py            # django-filter FilterSets (search pages)
│   ├── decorators.py         # allowed_users role-guard decorator
│   ├── admin.py              # Django admin registration
│   ├── apps.py
│   ├── tests.py
│   ├── templates/            # server-rendered HTML
│   │   ├── base.html, navbar.html, login.html, client.html, company.html, ...
│   │   ├── add/              # add client / staff / elevator / service
│   │   ├── update/           # update client / elevator / service
│   │   ├── delete/           # delete confirmation pages
│   │   ├── search/           # elevator search + service history
│   │   ├── messages/         # inbox, view / reply / send message
│   │   └── payment/          # Stripe checkout + success pages
│   └── static/               # CSS (compiled from SCSS), JS, images
│
└── docs/                     # project documentation
    ├── Elevator Service Manager - API Documentation.md
    ├── Elevator Service Manager - System Design.md
    └── Elevator Service Manager - Database Design.md
```

> Not tracked in git (created at runtime / kept local): `db.sqlite3`, the
> `media/` folder of user uploads, `.env`, and `__pycache__/`. Migrations are
> generated on first setup — see step 5 below.

## Getting started

### 1. Prerequisites

- Python 3.9 (the project was built and pinned against 3.9)
- pip

### 2. Clone and create a virtual environment

```bash
git clone https://github.com/evangelosvlachos96-dotcom/elevator-service-manager.git
cd elevator-service-manager
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in the values:

```bash
cp .env.example .env
```

Generate a fresh `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Add your Stripe **test** keys from <https://dashboard.stripe.com/apikeys>.

### 5. Set up the database

The repository does not ship a database. Create the schema with:

```bash
python manage.py makemigrations core
python manage.py migrate
```

### 6. Create the user groups

The app expects two Django Groups named **`Company`** and **`Client`**.
Create a superuser, then add the groups from the admin site:

```bash
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/admin/>, go to **Groups**, and create `Company`
and `Client`. Assign your superuser to the `Company` group so you can log in
to the staff dashboard. From there you can add clients and staff through the UI.

### 7. Run

```bash
python manage.py runserver
```

The app is served at <http://127.0.0.1:8000/>. The login page is the site root.

## Documentation

- **[API Documentation](docs/Elevator%20Service%20Manager%20-%20API%20Documentation.md)**
  — every URL route, its method, parameters, required role and what it returns.
- **[System Design](docs/Elevator%20Service%20Manager%20-%20System%20Design.md)**
  — architecture overview, request lifecycle, roles and permissions, the
  messaging and payment flows.
- **[Database Design](docs/Elevator%20Service%20Manager%20-%20Database%20Design.md)**
  — all models, fields, relationships and an entity-relationship overview.

## Security notes

- Secrets (`SECRET_KEY`, Stripe keys) are read from a `.env` file via
  `python-decouple` and are **not** committed. `.env` and `db.sqlite3` are
  git-ignored.
- This is a learning/portfolio project. Before any real deployment you would
  need to: set `DEBUG=False`, configure `ALLOWED_HOSTS`, serve static/media
  files properly, move off SQLite, and verify the Stripe Checkout success path
  against a webhook rather than a redirect.
