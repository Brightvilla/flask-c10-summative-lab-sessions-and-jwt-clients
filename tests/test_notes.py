from server import db
from server.models import Note


def make_note(client, auth_headers, title="Test Note", content="Some content", category="work"):
    return client.post("/notes", json={
        "title": title, "content": content, "category": category
    }, headers=auth_headers)


class TestNotesIndex:
    def test_get_notes_authenticated(self, client, auth_headers):
        make_note(client, auth_headers)
        resp = client.get("/notes", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "notes" in data
        assert "total" in data
        assert "pages" in data
        assert "page" in data

    def test_get_notes_unauthenticated(self, client):
        resp = client.get("/notes")
        assert resp.status_code == 401

    def test_pagination(self, client, auth_headers):
        for i in range(12):
            make_note(client, auth_headers, title=f"Note {i}", content="content")
        resp = client.get("/notes?page=1&per_page=5", headers=auth_headers)
        data = resp.get_json()
        assert len(data["notes"]) == 5
        assert data["total"] == 12
        assert data["pages"] == 3

    def test_users_cannot_see_others_notes(self, client, auth_headers, app):
        make_note(client, auth_headers)

        # create second user and their note
        resp2 = client.post("/signup", json={
            "username": "user2", "password": "pass", "password_confirmation": "pass"
        })
        token2 = resp2.get_json()["token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        make_note(client, headers2, title="User2 Note", content="private")

        resp = client.get("/notes", headers=auth_headers)
        notes = resp.get_json()["notes"]
        assert all(n["title"] != "User2 Note" for n in notes)


class TestCreateNote:
    def test_create_note_success(self, client, auth_headers):
        resp = make_note(client, auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "Test Note"
        assert data["category"] == "work"

    def test_create_note_missing_title(self, client, auth_headers):
        resp = client.post("/notes", json={"content": "content"}, headers=auth_headers)
        assert resp.status_code == 422

    def test_create_note_unauthenticated(self, client):
        resp = client.post("/notes", json={"title": "t", "content": "c"})
        assert resp.status_code == 401


class TestGetNote:
    def test_get_own_note(self, client, auth_headers):
        note_id = make_note(client, auth_headers).get_json()["id"]
        resp = client.get(f"/notes/{note_id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_other_users_note(self, client, auth_headers):
        resp2 = client.post("/signup", json={
            "username": "user3", "password": "pass", "password_confirmation": "pass"
        })
        headers2 = {"Authorization": f"Bearer {resp2.get_json()['token']}"}
        note_id = make_note(client, headers2).get_json()["id"]

        resp = client.get(f"/notes/{note_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestUpdateNote:
    def test_update_own_note(self, client, auth_headers):
        note_id = make_note(client, auth_headers).get_json()["id"]
        resp = client.patch(f"/notes/{note_id}", json={"title": "Updated"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "Updated"

    def test_update_other_users_note(self, client, auth_headers):
        resp2 = client.post("/signup", json={
            "username": "user4", "password": "pass", "password_confirmation": "pass"
        })
        headers2 = {"Authorization": f"Bearer {resp2.get_json()['token']}"}
        note_id = make_note(client, headers2).get_json()["id"]

        resp = client.patch(f"/notes/{note_id}", json={"title": "Hacked"}, headers=auth_headers)
        assert resp.status_code == 404


class TestDeleteNote:
    def test_delete_own_note(self, client, auth_headers):
        note_id = make_note(client, auth_headers).get_json()["id"]
        resp = client.delete(f"/notes/{note_id}", headers=auth_headers)
        assert resp.status_code == 200

        resp = client.get(f"/notes/{note_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_other_users_note(self, client, auth_headers):
        resp2 = client.post("/signup", json={
            "username": "user5", "password": "pass", "password_confirmation": "pass"
        })
        headers2 = {"Authorization": f"Bearer {resp2.get_json()['token']}"}
        note_id = make_note(client, headers2).get_json()["id"]

        resp = client.delete(f"/notes/{note_id}", headers=auth_headers)
        assert resp.status_code == 404
