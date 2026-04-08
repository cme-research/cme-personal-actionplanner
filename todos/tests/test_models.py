import datetime

import pytest
from django.contrib.auth import get_user_model

from todos.models import ActivityLog, Subtask, TodoItem, Topic

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def topic(db):
    return Topic.objects.create(name="Business")


@pytest.fixture
def todo_item(user, topic):
    return TodoItem.objects.create(
        name="Test Todo",
        description="Test description",
        due_date=datetime.date.today(),
        priority=TodoItem.Priority.HIGH,
        topic=topic,
        owner=user,
    )


class TestTopic:
    def test_str(self, topic):
        assert str(topic) == "Business"


class TestTodoItem:
    def test_str(self, todo_item):
        assert str(todo_item) == "Test Todo"

    def test_default_state(self, todo_item):
        assert todo_item.state == TodoItem.State.NEW

    def test_is_due_today(self, todo_item):
        assert todo_item.is_due_today is True

    def test_is_overdue(self, user):
        item = TodoItem.objects.create(
            name="Overdue",
            due_date=datetime.date.today() - datetime.timedelta(days=1),
            owner=user,
        )
        assert item.is_overdue is True

    def test_finished_not_overdue(self, user):
        item = TodoItem.objects.create(
            name="Done",
            due_date=datetime.date.today() - datetime.timedelta(days=1),
            state=TodoItem.State.FINISHED,
            owner=user,
        )
        assert item.is_overdue is False


class TestSubtask:
    def test_create_subtask(self, todo_item):
        subtask = Subtask.objects.create(
            todo_item=todo_item, name="Sub 1", position=0
        )
        assert subtask.is_completed is False
        assert str(subtask) == "Sub 1"


class TestActivityLog:
    def test_create_log(self, todo_item):
        log = ActivityLog.objects.create(
            todo_item=todo_item, action="created", detail="test"
        )
        assert "created" in str(log)
