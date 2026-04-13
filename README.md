# Flask Notes API — Sessions & JWT Auth Lab

## Project Description

A secure RESTful Flask API backend for a personal **Notes** app. Users can register, log in, and manage their own private notes. Authentication is handled via **JWT** (`Authorization: Bearer <token>`).

Key features:
- User registration and login with bcrypt password hashing
- JWT-based authentication and session persistence
- Full CRUD for user-owned notes
- Ownership enforcement — users cannot view or modify each other's notes
- Paginated notes listing
- Two ready-to-use React frontends (JWT and Sessions)

---

## Project Structure

```
.
├── server/
│   ├── app.py          # All routes and REST resources
│   ├── config.py       # Flask app, extensions, and DB configuration
│   ├── models.py       # SQLAlchemy models: User, Note
│   ├── seed.py         # Database seeding script (Faker)
│   └── Pipfile         # Python dependencies
├── client-with-jwt/    # JWT React frontend (port 4000)
├── client-with-sessions/ # Sessions React frontend (port 4000)
└── README.md
```

---

## Installation

### Prerequisites
- Python 3.8.13
- pipenv

```bash
cd server
pipenv install
pipenv shell
```

> If `pipenv install` fails to lock (known issue with some pipenv versions), install directly:
> ```bash
> pipenv run pip install flask==2.2.2 flask-sqlalchemy==3.0.3 Werkzeug==2.2.2 \
>   marshmallow==3.20.1 faker==15.3.2 flask-migrate==4.0.0 flask-restful==0.3.9 \
>   importlib-metadata==6.0.0 importlib-resources==5.10.0 flask-bcrypt==1.0.1 \
>   flask-jwt-extended pytest==7.2.0
> ```

### Migrate and seed the database

```bash
flask db init
flask db migrate -m "initial migration"
flask db upgrade
python seed.py
```

---

## Run the Server

```bash
flask run --port=5555
```

The API will be available at `http://localhost:5555`.

---

## Run a Frontend Client

```bash
# JWT client
cd client-with-jwt
npm install
npm start

# OR Sessions client
cd client-with-sessions
npm install
npm start
```

Both clients run on port **4000** and proxy API requests to `http://localhost:5555`.

---

## Models

### User
| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key |
| `username` | String(80) | Unique, not null |
| `_password_hash` | String(128) | Not null (bcrypt) |

### Note
| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key |
| `title` | String(120) | Not null |
| `body` | Text | Not null |
| `user_id` | Integer | Foreign key → users.id |

---

## API Endpoints

### Auth

| Method | Route | Auth Required | Description |
|---|---|---|---|
| `POST` | `/signup` | No | Register a new user, returns JWT + user |
| `POST` | `/login` | No | Authenticate user, returns JWT + user |
| `GET` | `/me` | Yes | Return current authenticated user |

#### POST `/signup`

Request body:
```json
{
  "username": "alice",
  "password": "secret123",
  "password_confirmation": "secret123"
}
```

Response `201`:
```json
{
  "token": "<JWT string>",
  "user": { "id": 1, "username": "alice" }
}
```

Error responses:
- `422` — missing fields, passwords don't match, or username taken

#### POST `/login`

Request body:
```json
{
  "username": "alice",
  "password": "secret123"
}
```

Response `200`:
```json
{
  "token": "<JWT string>",
  "user": { "id": 1, "username": "alice" }
}
```

Error responses:
- `401` — invalid username or password

#### GET `/me`

Headers: `Authorization: Bearer <token>`

Response `200`:
```json
{ "id": 1, "username": "alice" }
```

---

### Notes (JWT protected)

All notes endpoints require the header: `Authorization: Bearer <token>`

| Method | Route | Description |
|---|---|---|
| `GET` | `/notes` | List current user's notes (paginated) |
| `POST` | `/notes` | Create a new note |
| `GET` | `/notes/<id>` | Get a single note |
| `PATCH` | `/notes/<id>` | Update a note |
| `DELETE` | `/notes/<id>` | Delete a note |

#### GET `/notes?page=1&per_page=10`

Response `200`:
```json
{
  "notes": [{ "id": 1, "title": "My Note", "body": "...", "user_id": 1 }],
  "total": 6,
  "pages": 1,
  "page": 1
}
```

#### POST `/notes`

Request body:
```json
{ "title": "My Note", "body": "Note content here." }
```

Response `201`:
```json
{ "id": 1, "title": "My Note", "body": "Note content here.", "user_id": 1 }
```

Error responses:
- `422` — title or body missing

#### GET `/notes/<id>`

Response `200`: note object

Error responses:
- `404` — note not found
- `403` — note belongs to another user

#### PATCH `/notes/<id>`

Request body (any subset of fields):
```json
{ "title": "Updated Title" }
```

Response `200`: updated note object

Error responses:
- `404` — note not found
- `403` — note belongs to another user

#### DELETE `/notes/<id>`

Response `204`: empty body

Error responses:
- `404` — note not found
- `403` — note belongs to another user

---

## requirements.txt

The `requirements.txt` file at the project root lists all Python dependencies with pinned versions. It was generated from the active virtualenv using:

```bash
pip freeze > requirements.txt
```

To install from it, activate a virtual environment first then run:

```bash
# create and activate a virtualenv
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# install all dependencies
pip install -r requirements.txt
```

This ensures everyone working on the project uses the exact same package versions.

---

## Pipfile Dependencies

```toml
[packages]
flask = "2.2.2"
flask-sqlalchemy = "3.0.3"
Werkzeug = "2.2.2"
marshmallow = "3.20.1"
faker = "15.3.2"
flask-migrate = "4.0.0"
flask-restful = "0.3.9"
importlib-metadata = "6.0.0"
importlib-resources = "5.10.0"
flask-bcrypt = "1.0.1"
flask-jwt-extended = "*"

[dev-packages]
pytest = "7.2.0"
```

---

## Seed Data

Running `python seed.py` creates:
- **5 users** with username and hashed password (`password123`)
- **6 notes per user** (30 notes total) with Faker-generated titles and bodies

---

## Security

- Passwords are hashed with **bcrypt** — never stored in plain text
- JWT secret key should be changed to a strong random value in production
- All notes endpoints verify ownership — a `403` is returned if a user tries to access another user's note
