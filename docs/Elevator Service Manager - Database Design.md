# Database Design

The application uses SQLite (`db.sqlite3`) through the Django ORM. All
application models live in `core/models.py`. In addition to the tables below,
Django creates its own tables for authentication groups/permissions, sessions,
admin logs and content types — the most relevant of those is **`auth_group`**,
because user roles are modelled as group membership.

## 1. Entity-relationship overview

```
        auth_group (Company / Client / Administrator)
              │  (many-to-many: a User belongs to Group[s])
              ▼
        ┌───────────┐
        │   User    │  custom user (extends AbstractUser)
        └─────┬─────┘
              │ 1
        ┌─────┴───────────────────────────┬──────────────────────┐
        │ client_id (CASCADE)             │ stuff_id (SET_NULL)   │ sender (CASCADE)
        ▼ *                               │ *                     ▼ *
   ┌───────────┐                          │                 ┌───────────┐
   │ elevators │                          │                 │  Message  │
   └─────┬─────┘                          │                 └───────────┘
         │ 1                              │
         │ elevator_id (CASCADE)          │
         ▼ *                              │
   ┌───────────┐                          │
   │  service  │◄─────────────────────────┘
   └───────────┘

   ┌───────────┐
   │   week    │  standalone — no foreign keys (linked by username string)
   └───────────┘
```

Legend: `1` = one side, `*` = many side. `CASCADE` / `SET_NULL` is the
`on_delete` behaviour of the foreign key.

## 2. Tables

### 2.1 `User`

Custom user model (`AUTH_USER_MODEL = 'core.User'`), extending Django's
`AbstractUser`, so it also has `username`, `password`, `first_name`,
`last_name`, `is_staff`, `is_active`, `date_joined`, etc.

| Field          | Type                  | Notes |
|----------------|-----------------------|-------|
| `id`           | AutoField (PK)        | Inherited. |
| `username`     | CharField             | Inherited; unique login. |
| `password`     | CharField             | Inherited; hashed. |
| `first_name`   | CharField             | Inherited. |
| `last_name`    | CharField             | Inherited; used as the display "surname" in filters. |
| `email`        | EmailField            | **Required and unique** (overrides the default). |
| `profile_pic`  | ImageField            | Nullable; uploaded to `media/`. |
| `phone_number` | CharField(20)         | |
| `address`      | CharField(30)         | |
| `region`       | CharField(20)         | |

**Role:** determined by membership in `auth_group` (`Company`, `Client`, or
`Administrator`) — there is no role column on the table.

### 2.2 `elevators`

One physical elevator that the company maintains.

| Field            | Type                    | Notes |
|------------------|-------------------------|-------|
| `id`             | CharField(200) (PK)     | **Natural key** — a human-supplied unique elevator identifier, not an auto integer. |
| `client_id`      | FK → `User`             | The owner. `on_delete=CASCADE`, `limit_choices_to` group `Client`. Deleting the client deletes their elevators. |
| `elevator_type`  | CharField, choices      | `Hydraulic` or `Mechanical`. Nullable. |
| `moter_cauldron` | CharField(20)           | Motor cauldron spec. Nullable. |
| `control_panel`  | CharField(20)           | Nullable. |
| `book_code`      | CharField(20)           | Unique, nullable — the elevator's logbook code. |
| `watt`           | CharField(20)           | Nullable/blank. |
| `station`        | PositiveIntegerField    | Number of stops/stations. Nullable. |
| `wire_ropes`     | PositiveIntegerField    | Number of wire ropes. Nullable. |
| `chassi`         | CharField(20)           | Chassis identifier. Nullable/blank. |
| `last_kteo`      | DateField               | Date of last KTEO (statutory inspection). Nullable. |
| `comment`        | CharField(100)          | Free-text note. Nullable/blank. |

### 2.3 `service`

One service visit performed on an elevator.

| Field         | Type                  | Notes |
|---------------|-----------------------|-------|
| `id`          | AutoField (PK)        | |
| `elevator_id` | FK → `elevators` (`to_field='id'`) | `on_delete=CASCADE` — deleting the elevator deletes its service history. |
| `stuff_id`    | FK → `User`           | The technician who performed it. `on_delete=SET_NULL`, nullable, `limit_choices_to` group `Company`. `related_name='test_name'`. |
| `cost`        | PositiveIntegerField  | Required. Cost in euros. |
| `recipe_code` | CharField(50)         | Unique receipt/invoice code. Nullable/blank. |
| `date_ekd`    | DateField             | "EKD" issue date. Nullable/blank. |
| `date_ejof`   | DateField             | "EJOF" date. Nullable/blank. |
| `date`        | DateField             | Service date. Defaults to `now`. Nullable. |
| `comment`     | CharField(500)        | Client-editable comment on the service. Nullable/blank. |

### 2.4 `Message`

An internal message between a client and staff (or a broadcast).

| Field                 | Type                       | Notes |
|-----------------------|----------------------------|-------|
| `id`                  | AutoField (PK)             | |
| `sender`              | FK → `User`                | `on_delete=CASCADE`. |
| `receiver`            | CharField(200)             | **Stored as a username string, not a FK.** Nullable. |
| `elvtr`               | CharField(200)             | Elevator id this message is about (for `Alert` messages). Nullable/blank. |
| `message_type`        | CharField, choices         | `Alert` or `Simple`. Default `Simple`. |
| `categorized_problems`| CharField, choices         | For alerts: `Door Locked`, `Black out`, `Control Table`, `Station Level`, `Ropes Problem`. Nullable/blank. |
| `seen`                | BooleanField               | Read flag. Default `False`. |
| `date`                | DateTimeField              | Defaults to `now`. Nullable. |
| `text`                | CharField(200)             | Message body. Required. |
| `picture`             | ImageField                 | Optional attached photo, uploaded to `media/`. |

### 2.5 `week`

A rolling weekly technician shift roster. One row per week. **No foreign
keys** — it links to users only by storing usernames as strings.

| Field          | Type           | Notes |
|----------------|----------------|-------|
| `id`           | AutoField (PK) | Used with `.latest('id')` to find the current week. |
| `mon`–`sun`    | CharField(50)  | Seven columns, one per weekday; each holds the assigned technician's username. Nullable/blank. |
| `todays_shift` | CharField(50)  | Username of the technician currently on call — alert messages are routed here. Nullable/blank. |
| `week_year`    | CharField(50)  | The week's date label (set to `date.today()` when the row is auto-created on a Monday). Nullable/blank. |

## 3. Relationships summary

| From      | To          | Type        | FK field      | on_delete | Meaning |
|-----------|-------------|-------------|---------------|-----------|---------|
| `elevators` | `User`     | many-to-one | `client_id`   | CASCADE   | An elevator is owned by one client. |
| `service` | `elevators` | many-to-one | `elevator_id` | CASCADE   | A service belongs to one elevator. |
| `service` | `User`      | many-to-one | `stuff_id`    | SET_NULL  | A service was performed by one technician. |
| `Message` | `User`      | many-to-one | `sender`      | CASCADE   | A message was sent by one user. |
| `User`    | `auth_group`| many-to-many| (Django)      | —         | A user's role(s). |

## 4. Design notes and caveats

These are characteristics of the original 2021 design, kept as-is and
documented rather than changed:

- **String references instead of foreign keys.** `Message.receiver`,
  `Message.elvtr`, and every column of `week` store usernames / elevator ids
  as plain strings. This means there is no referential integrity on those
  links — renaming or deleting a user does not update them, and broadcasts
  duplicate rows per recipient.
- **Model naming.** Model classes `week`, `elevators` and `service` are
  lowercase/plural, which is unconventional for Django (normally singular
  PascalCase). `service.stuff_id` uses `related_name='test_name'`, which looks
  like a leftover placeholder.
- **Natural primary key on `elevators`.** `id` is a user-supplied string, so
  elevator ids must be unique and are passed directly in URLs.
- **No migrations in the repo.** The original `core/migrations/` folder is not
  present. Run `python manage.py makemigrations core` followed by
  `python manage.py migrate` to build the schema from `models.py`.
- **`db.sqlite3` is git-ignored.** The original database (which contained real
  user data and password hashes) is no longer committed; each environment
  builds its own.
