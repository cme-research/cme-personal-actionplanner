import datetime
import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from todos.models import Note, Subtask, TodoItem, Topic

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="otheruser", password="otherpass123")


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
        due_date=datetime.date.today(),
        priority=TodoItem.Priority.HIGH,
        topic=topic,
        owner=user,
    )


# --- Dashboard ---


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

    def test_dashboard_excludes_finished(self, client, user, topic):
        TodoItem.objects.create(
            name="Done Item", state=TodoItem.State.FINISHED, topic=topic, owner=user
        )
        response = client.get("/")
        assert b"Done Item" not in response.content

    def test_dashboard_search(self, client, todo_item):
        response = client.get("/?q=Test")
        assert b"Test Item" in response.content

    def test_dashboard_search_no_match(self, client, todo_item):
        response = client.get("/?q=nonexistent")
        assert b"Test Item" not in response.content

    def test_dashboard_filter_by_priority(self, client, todo_item):
        response = client.get("/?priority=high")
        assert b"Test Item" in response.content
        response = client.get("/?priority=low")
        assert b"Test Item" not in response.content

    def test_dashboard_filter_by_topic(self, client, todo_item, topic):
        response = client.get(f"/?topic={topic.pk}")
        assert b"Test Item" in response.content


# --- CRUD ---


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

    def test_create_form_get(self, client):
        response = client.get("/create/")
        assert response.status_code == 200

    def test_detail_view(self, client, todo_item):
        response = client.get(f"/{todo_item.pk}/")
        assert response.status_code == 200
        assert b"Test Item" in response.content

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

    def test_edit_form_get(self, client, todo_item):
        response = client.get(f"/{todo_item.pk}/edit/")
        assert response.status_code == 200

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

    def test_change_state_invalid(self, client, todo_item):
        response = client.post(
            f"/{todo_item.pk}/state/",
            {"state": "invalid_state", "next": "/"},
        )
        assert response.status_code == 302
        todo_item.refresh_from_db()
        assert todo_item.state == TodoItem.State.NEW  # unchanged


# --- User isolation ---


class TestUserIsolation:
    def test_cannot_see_other_users_todo(self, client, other_user, topic):
        other_item = TodoItem.objects.create(
            name="Other User Item", topic=topic, owner=other_user
        )
        response = client.get(f"/{other_item.pk}/")
        assert response.status_code == 404

    def test_cannot_edit_other_users_todo(self, client, other_user, topic):
        other_item = TodoItem.objects.create(
            name="Other User Item", topic=topic, owner=other_user
        )
        response = client.post(
            f"/{other_item.pk}/edit/",
            {"name": "Hacked", "priority": "low", "state": "new", "recurrence": "none"},
        )
        assert response.status_code == 404

    def test_cannot_delete_other_users_todo(self, client, other_user, topic):
        other_item = TodoItem.objects.create(
            name="Other User Item", topic=topic, owner=other_user
        )
        response = client.post(f"/{other_item.pk}/delete/")
        assert response.status_code == 404
        assert TodoItem.objects.filter(pk=other_item.pk).exists()


# --- Subtasks ---


class TestSubtaskViews:
    def test_add_subtask(self, client, todo_item):
        response = client.post(
            f"/{todo_item.pk}/subtask/add/", {"name": "Sub 1"}
        )
        assert response.status_code == 302
        assert todo_item.subtasks.filter(name="Sub 1").exists()

    def test_toggle_subtask(self, client, todo_item):
        subtask = Subtask.objects.create(
            todo_item=todo_item, name="Sub 1", position=0
        )
        response = client.post(f"/subtask/{subtask.id}/toggle/")
        assert response.status_code == 302
        subtask.refresh_from_db()
        assert subtask.is_completed is True

    def test_toggle_subtask_back(self, client, todo_item):
        subtask = Subtask.objects.create(
            todo_item=todo_item, name="Sub 1", is_completed=True
        )
        client.post(f"/subtask/{subtask.id}/toggle/")
        subtask.refresh_from_db()
        assert subtask.is_completed is False

    def test_delete_subtask(self, client, todo_item):
        subtask = Subtask.objects.create(
            todo_item=todo_item, name="Sub 1", position=0
        )
        response = client.post(f"/subtask/{subtask.id}/delete/")
        assert response.status_code == 302
        assert not Subtask.objects.filter(id=subtask.id).exists()


# --- Notes ---


class TestNoteViews:
    def test_add_note(self, client, todo_item):
        response = client.post(
            f"/{todo_item.pk}/note/add/", {"content": "My note"}
        )
        assert response.status_code == 302
        assert todo_item.notes.filter(content="My note").exists()

    def test_delete_note(self, client, todo_item):
        note = Note.objects.create(todo_item=todo_item, content="Delete me")
        response = client.post(f"/note/{note.id}/delete/")
        assert response.status_code == 302
        assert not Note.objects.filter(id=note.id).exists()


# --- Reorder ---


class TestReorder:
    def test_reorder(self, client, user, topic):
        item1 = TodoItem.objects.create(name="A", topic=topic, owner=user, position=0)
        item2 = TodoItem.objects.create(name="B", topic=topic, owner=user, position=1)
        response = client.post(
            "/reorder/",
            json.dumps({"items": [str(item2.pk), str(item1.pk)]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        item1.refresh_from_db()
        item2.refresh_from_db()
        assert item2.position == 0
        assert item1.position == 1

    def test_reorder_invalid_json(self, client):
        response = client.post(
            "/reorder/", "not json", content_type="application/json"
        )
        assert response.status_code == 400


# --- Kanban ---


class TestKanban:
    def test_kanban_view(self, client, todo_item):
        response = client.get("/kanban/")
        assert response.status_code == 200

    def test_kanban_shows_active_items(self, client, todo_item):
        response = client.get("/kanban/")
        assert b"Test Item" in response.content


# --- Calendar ---


class TestCalendar:
    def test_calendar_view(self, client):
        response = client.get("/calendar/")
        assert response.status_code == 200

    def test_calendar_with_params(self, client):
        response = client.get("/calendar/?year=2026&month=6")
        assert response.status_code == 200
        assert b"June" in response.content

    def test_calendar_shows_items(self, client, todo_item):
        today = datetime.date.today()
        response = client.get(f"/calendar/?year={today.year}&month={today.month}")
        assert b"Test Item" in response.content


# --- Archive ---


class TestArchive:
    def test_archive_view(self, client):
        response = client.get("/archive/")
        assert response.status_code == 200

    def test_archive_shows_finished(self, client, user, topic):
        TodoItem.objects.create(
            name="Finished Item", state=TodoItem.State.FINISHED, topic=topic, owner=user
        )
        response = client.get("/archive/")
        assert b"Finished Item" in response.content

    def test_archive_shows_wont_do(self, client, user, topic):
        TodoItem.objects.create(
            name="Skipped Item", state=TodoItem.State.WONT_DO, topic=topic, owner=user
        )
        response = client.get("/archive/")
        assert b"Skipped Item" in response.content

    def test_archive_excludes_active(self, client, todo_item):
        response = client.get("/archive/")
        assert b"Test Item" not in response.content


# --- Topics ---


class TestTopics:
    def test_topic_list(self, client, topic):
        response = client.get("/topics/")
        assert response.status_code == 200
        assert b"Personal" in response.content

    def test_create_topic(self, client):
        response = client.post("/topics/create/", {"name": "Gardening"})
        assert response.status_code == 302
        assert Topic.objects.filter(name="Gardening").exists()

    def test_delete_topic(self, client, topic):
        response = client.post(f"/topics/{topic.pk}/delete/")
        assert response.status_code == 302
        assert not Topic.objects.filter(pk=topic.pk).exists()


# --- Export ---


class TestExport:
    def test_export_json(self, client, todo_item):
        response = client.get("/export/json/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]["name"] == "Test Item"

    def test_export_csv(self, client, todo_item):
        response = client.get("/export/csv/")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        assert b"Test Item" in response.content

    def test_export_invalid_format(self, client):
        response = client.get("/export/xml/")
        assert response.status_code == 400


# --- Recurring ---


class TestRecurring:
    def test_finishing_recurring_creates_next(self, client, user, topic):
        item = TodoItem.objects.create(
            name="Weekly Task",
            due_date=datetime.date.today(),
            recurrence=TodoItem.RecurrenceInterval.WEEKLY,
            topic=topic,
            owner=user,
        )
        client.post(
            f"/{item.pk}/state/",
            {"state": "finished", "next": "/"},
        )
        new_items = TodoItem.objects.filter(name="Weekly Task", state=TodoItem.State.NEW)
        assert new_items.count() == 1
        assert new_items.first().due_date == datetime.date.today() + datetime.timedelta(weeks=1)

    def test_finishing_non_recurring_no_new_item(self, client, todo_item):
        count_before = TodoItem.objects.count()
        client.post(
            f"/{todo_item.pk}/state/",
            {"state": "finished", "next": "/"},
        )
        assert TodoItem.objects.count() == count_before  # no new item
