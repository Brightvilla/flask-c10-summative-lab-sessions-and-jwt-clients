import pytest
from server import create_app, db as _db
from server.models import User, Note


@pytest.fixture(scope="session")
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret",
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function", autouse=True)
def clean_db(app):
    with app.app_context():
        yield
        _db.session.rollback()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def new_user(app):
    with app.app_context():
        user = User(username="testuser")
        user.password_hash = "password123"
        _db.session.add(user)
        _db.session.commit()
        return {"id": user.id, "username": user.username}


@pytest.fixture
def auth_headers(client, new_user):
    resp = client.post("/login", json={"username": "testuser", "password": "password123"})
    token = resp.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
