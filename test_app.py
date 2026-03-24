import pytest

# import app module first so all routes are registered
import app as _app_module  # noqa: F401
from config import app, db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def signup(client, username="alice", password="pass1234", confirmation=None):
    return client.post("/signup", json={
        "username": username,
        "password": password,
        "password_confirmation": confirmation or password,
    })


def login(client, username="alice", password="pass1234"):
    return client.post("/login", json={"username": username, "password": password})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── Signup ────────────────────────────────────────────────────────────────────

class TestSignup:
    def test_signup_success(self, client):
        res = signup(client)
        assert res.status_code == 201
        data = res.get_json()
        assert "token" in data
        assert data["user"]["username"] == "alice"

    def test_signup_missing_username(self, client):
        res = signup(client, username="")
        assert res.status_code == 422

    def test_signup_missing_password(self, client):
        res = client.post("/signup", json={"username": "alice", "password": "", "password_confirmation": ""})
        assert res.status_code == 422

    def test_signup_passwords_dont_match(self, client):
        res = signup(client, password="pass1234", confirmation="different")
        assert res.status_code == 422

    def test_signup_duplicate_username(self, client):
        signup(client)
        res = signup(client)
        assert res.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, client):
        signup(client)
        res = login(client)
        assert res.status_code == 200
        data = res.get_json()
        assert "token" in data
        assert data["user"]["username"] == "alice"

    def test_login_wrong_password(self, client):
        signup(client)
        res = login(client, password="wrongpass")
        assert res.status_code == 401

    def test_login_unknown_user(self, client):
        res = login(client, username="nobody")
        assert res.status_code == 401


# ── Me ────────────────────────────────────────────────────────────────────────

class TestMe:
    def test_me_authenticated(self, client):
        token = signup(client).get_json()["token"]
        res = client.get("/me", headers=auth_header(token))
        assert res.status_code == 200
        assert res.get_json()["username"] == "alice"

    def test_me_no_token(self, client):
        res = client.get("/me")
        assert res.status_code == 401

    def test_me_invalid_token(self, client):
        res = client.get("/me", headers={"Authorization": "Bearer badtoken"})
        assert res.status_code == 422


# ── Notes List ────────────────────────────────────────────────────────────────

class TestNoteList:
    def test_get_notes_empty(self, client):
        token = signup(client).get_json()["token"]
        res = client.get("/notes", headers=auth_header(token))
        assert res.status_code == 200
        data = res.get_json()
        assert data["notes"] == []
        assert data["total"] == 0

    def test_get_notes_pagination(self, client):
        token = signup(client).get_json()["token"]
        headers = auth_header(token)
        for i in range(5):
            client.post("/notes", json={"title": f"Note {i}", "body": "body"}, headers=headers)
        res = client.get("/notes?page=1&per_page=3", headers=headers)
        data = res.get_json()
        assert len(data["notes"]) == 3
        assert data["total"] == 5
        assert data["pages"] == 2

    def test_get_notes_requires_auth(self, client):
        res = client.get("/notes")
        assert res.status_code == 401

    def test_create_note_success(self, client):
        token = signup(client).get_json()["token"]
        res = client.post("/notes",
            json={"title": "My Note", "body": "Some content."},
            headers=auth_header(token))
        assert res.status_code == 201
        data = res.get_json()
        assert data["title"] == "My Note"
        assert data["body"] == "Some content."

    def test_create_note_missing_title(self, client):
        token = signup(client).get_json()["token"]
        res = client.post("/notes", json={"body": "content"}, headers=auth_header(token))
        assert res.status_code == 422

    def test_create_note_missing_body(self, client):
        token = signup(client).get_json()["token"]
        res = client.post("/notes", json={"title": "title"}, headers=auth_header(token))
        assert res.status_code == 422

    def test_create_note_requires_auth(self, client):
        res = client.post("/notes", json={"title": "t", "body": "b"})
        assert res.status_code == 401


# ── Note Detail ───────────────────────────────────────────────────────────────

class TestNoteDetail:
    def _create_note(self, client, token):
        return client.post("/notes",
            json={"title": "Test", "body": "Body"},
            headers=auth_header(token)).get_json()

    def test_get_note_success(self, client):
        token = signup(client).get_json()["token"]
        note = self._create_note(client, token)
        res = client.get(f"/notes/{note['id']}", headers=auth_header(token))
        assert res.status_code == 200
        assert res.get_json()["id"] == note["id"]

    def test_get_note_not_found(self, client):
        token = signup(client).get_json()["token"]
        res = client.get("/notes/9999", headers=auth_header(token))
        assert res.status_code == 404

    def test_get_note_forbidden(self, client):
        token_a = signup(client, username="alice").get_json()["token"]
        token_b = signup(client, username="bob").get_json()["token"]
        note = self._create_note(client, token_a)
        res = client.get(f"/notes/{note['id']}", headers=auth_header(token_b))
        assert res.status_code == 403

    def test_patch_note_success(self, client):
        token = signup(client).get_json()["token"]
        note = self._create_note(client, token)
        res = client.patch(f"/notes/{note['id']}",
            json={"title": "Updated"},
            headers=auth_header(token))
        assert res.status_code == 200
        assert res.get_json()["title"] == "Updated"

    def test_patch_note_forbidden(self, client):
        token_a = signup(client, username="alice").get_json()["token"]
        token_b = signup(client, username="bob").get_json()["token"]
        note = self._create_note(client, token_a)
        res = client.patch(f"/notes/{note['id']}",
            json={"title": "Hacked"},
            headers=auth_header(token_b))
        assert res.status_code == 403

    def test_patch_note_not_found(self, client):
        token = signup(client).get_json()["token"]
        res = client.patch("/notes/9999", json={"title": "x"}, headers=auth_header(token))
        assert res.status_code == 404

    def test_delete_note_success(self, client):
        token = signup(client).get_json()["token"]
        note = self._create_note(client, token)
        res = client.delete(f"/notes/{note['id']}", headers=auth_header(token))
        assert res.status_code == 204

    def test_delete_note_forbidden(self, client):
        token_a = signup(client, username="alice").get_json()["token"]
        token_b = signup(client, username="bob").get_json()["token"]
        note = self._create_note(client, token_a)
        res = client.delete(f"/notes/{note['id']}", headers=auth_header(token_b))
        assert res.status_code == 403

    def test_delete_note_not_found(self, client):
        token = signup(client).get_json()["token"]
        res = client.delete("/notes/9999", headers=auth_header(token))
        assert res.status_code == 404

    def test_users_only_see_own_notes(self, client):
        token_a = signup(client, username="alice").get_json()["token"]
        token_b = signup(client, username="bob").get_json()["token"]
        client.post("/notes", json={"title": "Alice note", "body": "body"},
            headers=auth_header(token_a))
        client.post("/notes", json={"title": "Bob note", "body": "body"},
            headers=auth_header(token_b))
        res = client.get("/notes", headers=auth_header(token_a))
        notes = res.get_json()["notes"]
        assert all(n["user_id"] != token_b for n in notes)
        assert len(notes) == 1
        assert notes[0]["title"] == "Alice note"
