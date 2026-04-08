import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from todos.models import TodoItem, Topic

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def client(user):
    c = Client()
    c.login(username="testuser", password="testpass123")
    return c


@pytest.fixture
def topic(db):
    return Topic.objects.create(name="Personal")


@pytest.fixture
def todo_item(user, topic):
    return TodoItem.objects.create(
        name="Test Item",
        description="Description",
        priority=TodoItem.Priority.HIGH,
        topic=topic,
        owner=user,
    )


class TestDashboard:
    def test_dashboard_requires_login(self, db):
        c = Client()
        response = c.get("/")
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_dashboard_authenticated(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_dashboard_shows_items(self, client, todo_item):
        response = client.get("/")
        assert b"Test Item" in response.content


class TestTodoCRUD:
    def test_create_todo(self, client, topic):
        response = client.post(
            "/create/",
            {
                "name": "New Todo",
                "description": "Desc",
                "priority": "medium",
                "state": "new",
                "recurrence": "none",
                "topic": topic.pk,
            },
        )
        assert response.status_code == 302
        assert TodoItem.objects.filter(name="New Todo").exists()

    def test_edit_todo(self, client, todo_item):
        response = client.post(
            f"/{todo_item.pk}/edit/",
            {
                "name": "Updated",
                "description": "Updated desc",
                "priority": "low",
                "state": "current_work",
                "recurrence": "none",
            },
        )
        assert response.status_code == 302
        todo_item.refresh_from_db()
        assert todo_item.name == "Updated"

    def test_delete_todo(self, client, todo_item):
        response = client.post(f"/{todo_item.pk}/delete/")
        assert response.status_code == 302
        assert not TodoItem.objects.filter(pk=todo_item.pk).exists()

    def test_change_state(self, client, todo_item):
        response = client.post(
            f"/{todo_item.pk}/state/",
            {"state": "current_work", "next": "/"},
        )
        assert response.status_code == 302
        todo_item.refresh_from_db()
        assert todo_item.state == "current_work"


class TestTopics:
    def test_create_topic(self, client):
        response = client.post("/topics/create/", {"name": "Gardening"})
        assert response.status_code == 302
        assert Topic.objects.filter(name="Gardening").exists()

    def test_delete_topic(self, client, topic):
        response = client.post(f"/topics/{topic.pk}/delete/")
        assert response.status_code == 302
        assert not Topic.objects.filter(pk=topic.pk).exists()


class TestExport:
    def test_export_json(self, client, todo_item):
        response = client.get("/export/json/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"

    def test_export_csv(self, client, todo_item):
        response = client.get("/export/csv/")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
