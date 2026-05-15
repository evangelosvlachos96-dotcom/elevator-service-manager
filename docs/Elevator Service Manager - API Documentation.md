# API / Endpoint Reference

This is a server-rendered Django application, not a JSON REST API. Most
"endpoints" are URL routes that return rendered HTML pages or issue HTTP
redirects. Three routes (`/config/`, `/create-checkout-session/...`,
`/success/`) are AJAX/JSON endpoints used by the Stripe payment flow.

All routes are defined in `core/urls.py` and handled by function-based views
in `core/views.py`. The Django admin is additionally mounted at `/admin/`.

## Conventions

- **Method** — `GET` renders a page or form; `POST` submits a form. Most views
  accept both: `GET` shows the form, `POST` processes it and redirects.
- **Auth** — almost every view is wrapped in `@login_required(login_url='login')`.
  Unauthenticated users are redirected to the login page.
- **Role** — views wrapped in `@allowed_users(allowed_roles=[...])` additionally
  check the user's Django Group. A user in the wrong group gets a plain-text
  "You are not authorized to view this page" response.
- **`<pk>`** — a primary key passed in the URL. For users/services it is the
  numeric id; for elevators it is the elevator's string id.

---

## Authentication

| Name    | URL          | Methods   | Role | Description |
|---------|--------------|-----------|------|-------------|
| `login` | `/`          | GET, POST | any  | Site root. `POST` authenticates `username`/`password`; on success redirects to `client` or `company` depending on the user's group. On failure re-renders with an error message. |
| `logout`| `/logout/`   | GET       | auth | Logs the user out and redirects to `login`. |

---

## Dashboards

| Name      | URL          | Methods   | Role            | Description |
|-----------|--------------|-----------|-----------------|-------------|
| `client`  | `/client/`   | GET       | Client          | Client dashboard: the elevators they own, service history for those elevators, count of unread messages, and the technician currently on shift. |
| `company` | `/company/`  | GET, POST | Company         | Staff dashboard: totals (clients, elevators, services, staff), elevator list with filters, the 10 most recent services, unread-message count, and the weekly shift schedule. `POST` saves the weekly shift schedule. Auto-creates a new `week` row on Mondays. |

---

## Clients

| Name             | URL                          | Methods   | Role    | Description |
|------------------|------------------------------|-----------|---------|-------------|
| `add_client`     | `/company/add_client/`       | GET, POST | Company | Create a new user and add them to the `Client` group. |
| `update_client`  | `/updateClient/<pk>/`        | GET, POST | auth    | Edit a user's profile fields (name, phone, address, region, email). Redirects to the caller's own dashboard. |
| `change_password`| `/changePassword/<pk>/`      | GET, POST | auth    | Change a user's password via the user-creation form. |
| `delete_client`  | `/deleteClient/<pk>/`        | GET, POST | Company | `GET` shows a confirmation page; `POST` deletes the client. |

## Staff

| Name           | URL                       | Methods   | Role    | Description |
|----------------|---------------------------|-----------|---------|-------------|
| `add_member`   | `/company/add_member/`    | GET, POST | Company | Create a new user and add them to the `Company` group. |
| `delete_stuff` | `/deleteStuff/<pk>/`      | GET, POST | Company | `GET` confirmation page; `POST` deletes the staff user. |

---

## Elevators

| Name             | URL                                | Methods   | Role    | Description |
|------------------|------------------------------------|-----------|---------|-------------|
| `add_elevator`   | `/company/add_elevator/<pk>/`      | GET, POST | Company | Register a new elevator for the client identified by `<pk>`. Uses an inline formset bound to the client. |
| `update_elevator`| `/updateElevator/<pk>/`            | GET, POST | auth    | Edit an elevator's details. |
| `delete_elevator`| `/deleteElevator/<pk>/`            | GET, POST | Company | `GET` confirmation page; `POST` deletes the elevator. |
| `elevator_card`  | `/elevatorCard/<pk>/`              | GET       | auth    | Detail page for one elevator plus all its service records. |
| `search_elevator`| `/searchElevator/`                 | GET       | Company | Elevator search page; filterable by id, book code, client, type and last-KTEO date. |

---

## Services

| Name             | URL                          | Methods   | Role    | Description |
|------------------|------------------------------|-----------|---------|-------------|
| `make_service`   | `/make_service/<pk>/`        | GET, POST | Company | Log a new service visit for the elevator identified by `<pk>`. |
| `update_service` | `/updateService/<pk>/`       | GET, POST | Company | Edit an existing service record. |
| `delete_service` | `/deleteService/<pk>/`       | GET, POST | Company | `GET` confirmation page; `POST` deletes the service record. |
| `service_comment`| `/createServiceComment/<pk>/`| GET, POST | Client  | Lets a client add/edit the free-text comment on a service. |
| `service_history`| `/serviceHistory/`           | GET       | Company | Service history page; filterable by elevator id, technician and date range. |

---

## Messaging

| Name                 | URL                                   | Methods   | Role   | Description |
|----------------------|---------------------------------------|-----------|--------|-------------|
| `send_alert_message` | `/alert-message/<pk>/<ig>/`           | GET, POST | Client | Report a categorized elevator fault. `<pk>` is the sender's user id, `<ig>` is the elevator id. The message is typed `Alert`, its receiver is set to the technician on shift today, and `elvtr` is set to the elevator id. Supports an optional photo upload. |
| `reply_message`      | `/reply-message/<pk>/`                | GET, POST | auth   | Reply to message `<pk>`; the new message's receiver is the original sender. |
| `simple_message`     | `/simple-message/`                    | GET, POST | auth   | Send a free-text message. Recipient can be a single user, **all clients** (`All`), or **all staff** (`tocompany`) — in the broadcast cases one message row is created per recipient. |
| `allMessages`        | `/allMessages/`                       | GET       | auth   | Inbox + sent list. Contents are scoped by role: `Client`/`Company` see messages addressed to them; `Administrator` sees messages from clients. Filterable by seen status, type and sender. |
| `messageview`        | `/viewMessage/<pk>/`                  | GET       | auth   | View a single message; marks it as `seen = True`. |

---

## Payments (Stripe Checkout)

| Name      | URL                                      | Methods | Role | Returns | Description |
|-----------|------------------------------------------|---------|------|---------|-------------|
| —         | `/config/`                               | GET     | any  | JSON    | Returns `{ "publicKey": <STRIPE_PUBLISHABLE_KEY> }` for the frontend Stripe.js to initialize. |
| —         | `/create-checkout-session/<pk>/`         | GET     | any  | JSON    | Creates a Stripe Checkout Session for an amount of `<pk>` euros (sent to Stripe as `pk * 100` cents). Returns `{ "sessionId": ... }` or `{ "error": ... }`. |
| —         | `/success/`                              | GET     | any  | HTML    | Stripe success-redirect landing page. |
| —         | `/cancelled/`                            | GET     | any  | HTML    | Stripe cancel-redirect landing page (class-based `TemplateView`). |

> Note: the `config` and `create-checkout-session` views are decorated with
> `@csrf_exempt` and only handle `GET`. Payment confirmation is done via a
> browser redirect, not a Stripe webhook.

---

## Admin

| URL        | Description |
|------------|-------------|
| `/admin/`  | Django admin site. `User` (with a customized form exposing phone/address/region/profile pic), `week`, `elevators`, `service` and `Message` are all registered. |

---

## Media

User-uploaded files (profile pictures, message photos) are served from
`/media/` during development via `static()` in `webapp/urls.py`.
