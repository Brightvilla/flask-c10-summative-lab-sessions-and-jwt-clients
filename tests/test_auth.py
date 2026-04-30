class TestSignup:
    def test_signup_success(self, client):
        resp = client.post("/signup", json={
            "username": "newuser",
            "password": "pass123",
            "password_confirmation": "pass123",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "token" in data
        assert data["user"]["username"] == "newuser"

    def test_signup_duplicate_username(self, client, new_user):
        resp = client.post("/signup", json={
            "username": "testuser",
            "password": "pass123",
            "password_confirmation": "pass123",
        })
        assert resp.status_code == 422
        assert "errors" in resp.get_json()

    def test_signup_password_mismatch(self, client):
        resp = client.post("/signup", json={
            "username": "anotheruser",
            "password": "pass123",
            "password_confirmation": "different",
        })
        assert resp.status_code == 422

    def test_signup_missing_username(self, client):
        resp = client.post("/signup", json={
            "username": "",
            "password": "pass123",
            "password_confirmation": "pass123",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client, new_user):
        resp = client.post("/login", json={"username": "testuser", "password": "password123"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert data["user"]["username"] == "testuser"

    def test_login_wrong_password(self, client, new_user):
        resp = client.post("/login", json={"username": "testuser", "password": "wrong"})
        assert resp.status_code == 401
        assert "errors" in resp.get_json()

    def test_login_unknown_user(self, client):
        resp = client.post("/login", json={"username": "nobody", "password": "pass"})
        assert resp.status_code == 401


class TestMe:
    def test_me_authenticated(self, client, auth_headers, new_user):
        resp = client.get("/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["username"] == "testuser"

    def test_me_unauthenticated(self, client):
        resp = client.get("/me")
        assert resp.status_code == 401
