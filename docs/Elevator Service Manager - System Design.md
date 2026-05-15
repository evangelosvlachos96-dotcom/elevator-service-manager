# System Design

## 1. Overview

Elevator Service Manager is a monolithic, server-rendered Django web
application. It serves a single business: an elevator maintenance company that
needs to track its clients, the elevators it maintains, the service visits it
performs, the technicians on duty, and the communication between clients and
staff. Clients also pay for service online.

There is no separate frontend or API tier — Django renders HTML templates
directly and the browser submits standard form `POST`s. The only JSON traffic
is the small AJAX exchange that bootstraps Stripe Checkout.

## 2. Architecture

```
                         ┌──────────────────────────────┐
                         │           Browser            │
                         │  HTML forms + vanilla JS      │
                         │  (login.js, payment.js,       │
                         │   script.js)                 │
                         └──────────────┬───────────────┘
                                        │ HTTP (GET/POST)
                                        ▼
        ┌───────────────────────────────────────────────────────┐
        │                  Django (webapp project)              │
        │                                                       │
        │  webapp/urls.py ──► core/urls.py                       │
        │        │                                              │
        │        ▼                                              │
        │  Middleware: security, sessions, csrf, auth, messages  │
        │        │                                              │
        │        ▼                                              │
        │  Decorators: @login_required, @allowed_users(role)     │
        │        │                                              │
        │        ▼                                              │
        │  core/views.py  (function-based views)                 │
        │     ├─ forms.py    (ModelForms / formsets)             │
        │     ├─ filters.py  (django-filter FilterSets)          │
        │     └─ models.py   (ORM)                               │
        │        │                                              │
        │        ▼                                              │
        │  Templates (core/templates/*.html)                     │
        └───────┬───────────────────────────────┬───────────────┘
                │                               │
                ▼                               ▼
        ┌───────────────┐               ┌───────────────────┐
        │  SQLite (db)  │               │   Stripe API      │
        │  db.sqlite3   │               │  (Checkout)       │
        └───────────────┘               └───────────────────┘
```

### Components

| Component        | Responsibility |
|------------------|----------------|
| `webapp/`        | Django project config: `settings.py` (now reading secrets from `.env` via `python-decouple`), root `urls.py`, `wsgi.py`/`asgi.py`. |
| `core/`          | The single app holding all business logic. |
| `core/models.py` | The data model — see [Database Design](<Elevator Service Manager - Database Design.md>). |
| `core/views.py`  | All request handlers. Function-based views, one per use case. |
| `core/forms.py`  | `ModelForm`s for users, elevators and services, plus `CustomUserCreationForm`. Some views build inline formsets directly. |
| `core/filters.py`| `django-filter` `FilterSet`s powering the search and message-list pages. |
| `core/decorators.py` | `allowed_users` — a role-guard decorator that inspects the user's first Django Group. |
| `core/templates/`| Server-rendered HTML, organised into `add/`, `update/`, `delete/`, `search/`, `messages/`, `payment/` folders plus a shared `base.html`/`navbar.html`. |
| `core/static/`   | CSS (compiled from SCSS), images, and three JS files. |
| `media/`         | User uploads: profile pictures and photos attached to messages. |

## 3. Request lifecycle

1. The browser issues a request to a path under `/`.
2. `webapp/urls.py` delegates everything (except `/admin/`) to `core/urls.py`,
   which maps the path to a view function.
3. Django middleware runs: session loading, CSRF checking (except the two
   `@csrf_exempt` Stripe config views), and authentication.
4. View decorators run:
   - `@login_required` redirects anonymous users to `/` (the login page).
   - `@allowed_users([...])` checks the user's group; a mismatch returns a
     plain "not authorized" `HttpResponse`.
5. The view executes:
   - On `GET` it queries the ORM, optionally applies a `FilterSet`, builds a
     context dict and renders a template.
   - On `POST` it binds a form/formset, validates, saves, and **redirects**
     (Post/Redirect/Get) to the relevant dashboard or list page.
6. The template is rendered to HTML and returned.

## 4. Roles and permissions

Authorization is built entirely on Django's `auth` Groups. There is **no role
field on the model** — a user's role is "the name of their first Group".

| Group           | Who                        | Can do |
|-----------------|----------------------------|--------|
| `Company`       | Technicians / office staff | Full management: add/update/delete clients, staff, elevators and services; view all dashboards, search and the weekly schedule. |
| `Client`        | Elevator owners            | View their own elevators and service history; report faults (`Alert` messages); comment on a completed service; pay for service. |
| `Administrator` | (referenced in views)      | A third group name the messaging/dashboard views branch on to see a company-wide view of messages. Not produced by the signup forms — it must be assigned manually in the admin. |

The custom `User` model (`AUTH_USER_MODEL = 'core.User'`) extends
`AbstractUser` with `phone_number`, `address`, `region`, `profile_pic` and a
unique `email`.

> **Design note / known sharp edges:** `allowed_users` reads `groups.all()[0]`,
> so a user is assumed to belong to exactly one group. Several edit views
> (`update_elevator`, `update_client`, `change_password`, `reply_message`,
> `viewMessage`) are guarded only by `@login_required`, not by role — any
> logged-in user can reach them if they know the URL.

## 5. Key flows

### 5.1 Login routing

`loginPage` authenticates the credentials, then reads `request.user.groups`
to decide the landing page: `Client` → `/client/`, `Company` → `/company/`.

### 5.2 Weekly shift schedule

The `week` model is a rolling roster (one row per week, with a column per
weekday plus `todays_shift`). When a `Company` user opens the dashboard on a
Monday, the view creates a fresh `week` row for that date if one does not
already exist. Staff submit the week's assignments via the dashboard `POST`.
`todays_shift` holds the username of the technician currently on call.

### 5.3 Alert messaging

When a client reports a fault (`send_alert_message`):
1. A `Message` is saved from the inline formset (category, text, optional photo).
2. The view then patches the just-created row: `message_type = 'Alert'`,
   `receiver = week.todays_shift` (the on-call technician's username), and
   `elvtr = <elevator id>`.

Simple messages can be addressed to one user or broadcast — broadcasting
creates one `Message` row per recipient. `viewMessage` flips `seen = True`
on open; dashboards count unread messages by filtering `seen = False`.

### 5.4 Stripe payment

1. The payment page JS calls `GET /config/` to get the publishable key and
   initialise Stripe.js.
2. JS calls `GET /create-checkout-session/<amount>/`; the server creates a
   Stripe Checkout Session (line item priced at `amount * 100` cents, EUR) and
   returns its `sessionId`.
3. Stripe.js redirects the browser to Stripe's hosted checkout.
4. Stripe redirects back to `/success/` or `/cancelled/`.

> The success path is a plain redirect — there is no webhook verifying the
> payment server-side, and no `service` row is updated on payment. This is
> acceptable for a demo but would need a webhook for production.

## 6. Configuration

Runtime configuration comes from a `.env` file (not committed) read by
`python-decouple`:

| Variable                  | Purpose |
|---------------------------|---------|
| `SECRET_KEY`              | Django cryptographic signing key. |
| `DEBUG`                   | Debug mode toggle. |
| `ALLOWED_HOSTS`           | Comma-separated hostnames (used when `DEBUG=False`). |
| `STRIPE_PUBLISHABLE_KEY`  | Stripe.js publishable key (sent to the browser). |
| `STRIPE_SECRET_KEY`       | Stripe server-side secret key. |

## 7. Deployment considerations

This is a development-grade project. To run it in production you would need to:

- Set `DEBUG=False` and a real `ALLOWED_HOSTS`.
- Replace SQLite with a server database (PostgreSQL).
- Serve static files via `collectstatic` + a real web server / CDN, and move
  media uploads to durable storage.
- Run under a WSGI server (gunicorn/uWSGI) behind nginx.
- Add a Stripe webhook to confirm payments instead of trusting the redirect.
- Add CSRF protection back to the payment config endpoints or replace them
  with a properly authenticated API.
- Rotate the `SECRET_KEY` and Stripe keys that were previously committed.

## 8. Technology choices

| Choice | Rationale |
|--------|-----------|
| Django monolith | Single developer, CRUD-heavy domain — Django's admin, ORM, auth, forms and templating cover almost the entire app with little custom code. |
| Function-based views | Straightforward one-handler-per-use-case style; easy to read. |
| SQLite | Zero-config local development database. |
| django-filter | Declarative search/filter UI for the elevator and service lists. |
| Groups for roles | Reuses Django's built-in permission primitives instead of a custom role system. |
| Stripe Checkout | Offloads all card handling and PCI scope to Stripe's hosted page. |
