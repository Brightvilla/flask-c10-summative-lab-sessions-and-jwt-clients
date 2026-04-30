# Notes App — Flask JWT Backend

A secure RESTful Flask API backend for a personal notes productivity app. Users can register, log in, and manage their own notes. Authentication is handled via JWT (JSON Web Tokens). All note routes are protected and scoped to the authenticated user.

---

## Installation

1. Clone the repository and navigate into it:

```bash
git clone <your-repo-url>
cd flask-c10-summative-lab-sessions-and-jwt-clients
```

2. Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask==2.2.2 flask-sqlalchemy==3.0.3 Werkzeug==2.2.2 marshmallow==3.20.1 \
  faker==15.3.2 flask-migrate==4.0.0 flask-restful==0.3.9 flask-bcrypt==1.0.1 \
  flask-jwt-extended pytest==7.2.0
```

3. Initialize and migrate the database:

```bash
flask --app app db init
flask --app app db migrate -m "initial migration"
flask --app app db upgrade
```

4. Seed the database with sample data:

```bash
python seed.py
```

---

## Running the App

```bash
flask --app app run --port 5555
```

The API will be available at `http://127.0.0.1:5555`.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## API Endpoints

### Auth

| Method | Endpoint  | Description | Auth Required |
|--------|-----------|-------------|---------------|
| POST   | `/signup` | Register a new user. Body: `{ username, password, password_confirmation }`. Returns `{ token, user }`. | No |
| POST   | `/login`  | Log in an existing user. Body: `{ username, password }`. Returns `{ token, user }`. | No |
| GET    | `/me`     | Returns the currently authenticated user. | Yes |

### Notes

| Method | Endpoint          | Description | Auth Required |
|--------|-------------------|-------------|---------------|
| GET    | `/notes`          | List all notes for the current user. Supports `?page=1&per_page=10` pagination. Returns `{ notes, total, pages, page }`. | Yes |
| POST   | `/notes`          | Create a new note. Body: `{ title, content, category (optional) }`. | Yes |
| GET    | `/notes/<id>`     | Get a single note by ID (must belong to current user). | Yes |
| PATCH  | `/notes/<id>`     | Update a note (must belong to current user). Body: any of `{ title, content, category }`. | Yes |
| DELETE | `/notes/<id>`     | Delete a note (must belong to current user). | Yes |

All protected routes require the header: `Authorization: Bearer <token>`

Unauthorized requests return `401`. Accessing another user's resource returns `404`.

---

## Project Structure

```
flask-c10-summative-lab-sessions-and-jwt-clients/
├── server/
│   ├── __init__.py      # App factory, extensions (db, bcrypt, jwt)
│   ├── models.py        # User + Note models
│   └── routes.py        # All route handlers
├── tests/
│   ├── conftest.py      # Fixtures (app, client, clean_db, new_user, auth_headers)
│   ├── test_auth.py     # Signup, login, /me tests
│   └── test_notes.py    # Full CRUD + pagination + access control tests
├── app.py               # Entry point
├── seed.py              # Seeds 3 users × 5 notes each
├── Pipfile              # Dependencies
├── pytest.ini           # Test config
└── README.md            # Docs
```

---

## Flask Backend & Postman

The Flask backend is just an API — it has no pages to display. It only responds to specific routes:

- `http://127.0.0.1:5555/signup` — handles user registration
- `http://127.0.0.1:5555/login` — handles user login
- `http://127.0.0.1:5555/me` — returns the logged in user
- `http://127.0.0.1:5555/notes` — handles notes CRUD

These routes don't return web pages — they return JSON data. For example hitting `/login` returns:

```json
{ "token": "eyJ...", "user": { "id": 1, "username": "john" } }
```

---

## React Frontend

The React frontend (`http://localhost:4000`) is the actual web page users interact with. Behind the scenes it talks to the Flask API to sign up, log in, and manage notes. Think of it like:

Browser (localhost:4000)  →  React App  →  Flask API (localhost:5555)

## How to Check if all the tests are passing

cd ~/flask-c10-summative-lab-sessions-and-jwt-clients
source .venv/bin/activate
python -m pytest tests/ -v
