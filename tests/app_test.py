from pathlib import Path

import pytest
from sqlalchemy import inspect

from project.app import create_app, db
from project.models import Post


@pytest.fixture
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "USERNAME": "tester",
        "PASSWORD": "test-password",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
    })
    with application.app_context():
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username=None, password=None):
    return client.post("/login", data={
        "username": username if username is not None else client.application.config["USERNAME"],
        "password": password if password is not None else client.application.config["PASSWORD"],
    }, follow_redirects=True)


@pytest.fixture
def posts(app):
    with app.app_context():
        entries = [Post("Flask testing", "Red green refactor"),
                   Post("Deployment", "A FLASK app on Render"),
                   Post("Unrelated", "Coffee break")]
        db.session.add_all(entries)
        db.session.commit()
        return [entry.id for entry in entries]


def test_index(client):
    assert client.get("/").status_code == 200


def test_database(app):
    with app.app_context():
        assert Path(db.engine.url.database).is_file()
        assert "post" in inspect(db.engine).get_table_names()
        assert db.session.query(Post).count() == 0


def test_empty_db(client):
    assert b"No entries yet. Add some!" in client.get("/").data


def test_login_logout(client):
    assert b"You were logged in" in login(client).data
    with client.session_transaction() as session:
        assert session["logged_in"] is True
    response = client.get("/logout", follow_redirects=True)
    assert b"You were logged out" in response.data
    with client.session_transaction() as session:
        assert "logged_in" not in session


@pytest.mark.parametrize("username,password,message", [
    ("wrong", "test-password", b"Invalid username"),
    ("tester", "wrong", b"Invalid password"),
])
def test_invalid_login(client, username, password, message):
    assert message in login(client, username, password).data
    with client.session_transaction() as session:
        assert not session.get("logged_in")


def test_messages(client, app):
    login(client)
    response = client.post("/add", data={"title": "<Hello>",
        "text": "<strong>HTML</strong> allowed here"}, follow_redirects=True)
    assert b"No entries yet. Add some!" not in response.data
    assert b"&lt;Hello&gt;" in response.data
    assert b"<strong>HTML</strong> allowed here" in response.data
    with app.app_context():
        assert db.session.query(Post).count() == 1


def test_add_requires_login(client, app):
    assert client.post("/add", data={"title": "No", "text": "No"}).status_code == 401
    with app.app_context():
        assert db.session.query(Post).count() == 0


@pytest.mark.parametrize("data", [
    {}, {"title": "Title"}, {"title": "", "text": "Body"},
    {"title": "Title", "text": "   "},
])
def test_add_rejects_incomplete_posts(client, app, data):
    login(client)
    assert client.post("/add", data=data).status_code == 400
    with app.app_context():
        assert db.session.query(Post).count() == 0


def test_delete_message(client, app, posts):
    login(client)
    response = client.get(f"/delete/{posts[0]}")
    assert response.status_code == 200
    assert response.json["status"] == 1
    with app.app_context():
        assert db.session.get(Post, posts[0]) is None
        assert db.session.query(Post).count() == 2
    assert b"Flask testing" not in client.get("/").data


def test_delete_requires_login(client, app, posts):
    response = client.get(f"/delete/{posts[0]}")
    assert response.status_code == 401
    assert response.json == {"status": 0, "message": "Please log in."}
    with app.app_context():
        assert db.session.get(Post, posts[0]) is not None


def test_logout_revokes_delete_access(client, app, posts):
    login(client)
    client.get("/logout")
    assert client.get(f"/delete/{posts[0]}").status_code == 401
    with app.app_context():
        assert db.session.get(Post, posts[0]) is not None


def test_delete_missing_post(client):
    login(client)
    response = client.get("/delete/999999")
    assert response.status_code == 404
    assert response.json["status"] == 0


def test_delete_invalid_id(client, app, posts):
    login(client)
    assert client.get("/delete/1%20OR%201=1").status_code == 404
    with app.app_context():
        assert db.session.query(Post).count() == 3


def test_search_page_without_query(client, posts):
    response = client.get("/search/")
    assert response.status_code == 200
    assert b"Flask testing" not in response.data


@pytest.mark.parametrize("query,expected,excluded", [
    ("flask", [b"Flask testing", b"Deployment"], [b"Unrelated"]),
    ("rEfAcToR", [b"Flask testing"], [b"Deployment", b"Unrelated"]),
    ("Render", [b"Deployment"], [b"Flask testing", b"Unrelated"]),
])
def test_search_filters_title_and_body_case_insensitively(client, posts, query, expected, excluded):
    response = client.get("/search/", query_string={"query": query})
    assert response.status_code == 200
    for title in expected:
        assert title in response.data
    for title in excluded:
        assert title not in response.data


def test_search_no_match(client, posts):
    assert b"No matching entries." in client.get("/search/?query=nomatch").data


def test_search_blank_query(client, posts):
    response = client.get("/search/?query=%20%20")
    assert response.status_code == 200
    assert b"Flask testing" not in response.data


def test_search_result_has_correct_delete_id(client, posts):
    login(client)
    response = client.get("/search/?query=refactor")
    assert f'id="{posts[0]}"'.encode() in response.data


def test_search_escapes_query(client):
    response = client.get("/search/", query_string={"query": "<script>alert(1)</script>"})
    assert b"<script>alert(1)</script>" not in response.data


def test_post_html_is_sanitized(client):
    login(client)
    response = client.post("/add", data={"title": "Markup", "text":
        '<strong>OK</strong><script>alert(1)</script><img src=x onerror=alert(2)>'},
        follow_redirects=True)
    assert b"<strong>OK</strong>" in response.data
    assert b"<script>alert(1)" not in response.data
    assert b"onerror=" not in response.data


def test_index_orders_newest_first(client, posts):
    html = client.get("/").data
    assert html.index(b"Unrelated") < html.index(b"Deployment") < html.index(b"Flask testing")


def test_independent_app_database(app, tmp_path):
    other = create_app({"TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'other.db'}"})
    with app.app_context():
        db.session.add(Post("Keep me", "Original database"))
        db.session.commit()
    with other.app_context():
        db.create_all()
        assert db.session.query(Post).count() == 0
        db.drop_all()
        db.session.remove()
        db.engine.dispose()
    with app.app_context():
        assert db.session.query(Post).one().title == "Keep me"


def test_postgres_url_normalization(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:password@localhost/example")
    application = create_app({"TESTING": True})
    assert application.config["SQLALCHEMY_DATABASE_URI"] == "postgresql://user:password@localhost/example"
    with application.app_context():
        db.engine.dispose()
