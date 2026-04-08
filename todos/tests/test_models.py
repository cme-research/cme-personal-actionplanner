import datetime

import pytest
from django.contrib.auth import get_user_model

from todos.models import ActivityLog, Attachment, Note, Subtask, TodoItem, Topic

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

    def test_unique_name(self, topic, db):
        with pytest.raises(Exception):
            Topic.objects.create(name="Business")

    def test_ordering(self, db):
        Topic.objects.create(name="Zebra")
        Topic.objects.create(name="Alpha")
        names = list(Topic.objects.values_list("name", flat=True))
        assert names == sorted(names)


class TestTodoItem:
    def test_str(self, todo_item):
        assert str(todo_item) == "Test Todo"

    def test_default_state(self, todo_item):
        assert todo_item.state == TodoItem.State.NEW

    def test_default_priority(self, user):
        item = TodoItem.objects.create(name="Default", owner=user)
        assert item.priority == TodoItem.Priority.MEDIUM

    def test_is_due_today(self, todo_item):
        assert todo_item.is_due_today is True

    def test_is_due_today_false(self, user):
        item = TodoItem.objects.create(
            name="Tomorrow",
            due_date=datetime.date.today() + datetime.timedelta(days=1),
            owner=user,
        )
        assert item.is_due_today is False

    def test_is_due_today_no_date(self, user):
        item = TodoItem.objects.create(name="No date", owner=user)
        assert item.is_due_today is False

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

    def test_wont_do_not_overdue(self, user):
        item = TodoItem.objects.create(
            name="Skipped",
            due_date=datetime.date.today() - datetime.timedelta(days=1),
            state=TodoItem.State.WONT_DO,
            owner=user,
        )
        assert item.is_overdue is False

    def test_no_date_not_overdue(self, user):
        item = TodoItem.objects.create(name="No date", owner=user)
        assert item.is_overdue is False

    def test_is_due_this_week(self, user):
        today = datetime.date.today()
        end_of_week = today + datetime.timedelta(days=(6 - today.weekday()))
        item = TodoItem.objects.create(
            name="This week", due_date=end_of_week, owner=user
        )
        assert item.is_due_this_week is True

    def test_is_due_this_week_false(self, user):
        item = TodoItem.objects.create(
            name="Next week",
            due_date=datetime.date.today() + datetime.timedelta(days=14),
            owner=user,
        )
        assert item.is_due_this_week is False

    def test_is_due_this_week_no_date(self, user):
        item = TodoItem.objects.create(name="No date", owner=user)
        assert item.is_due_this_week is False

    def test_estimation_field(self, user):
        item = TodoItem.objects.create(
            name="Estimated",
            estimation=datetime.timedelta(hours=2, minutes=30),
            owner=user,
        )
        assert item.estimation == datetime.timedelta(hours=2, minutes=30)

    def test_cascade_delete_with_user(self, user, todo_item):
        user.delete()
        assert not TodoItem.objects.filter(pk=todo_item.pk).exists()

    def test_topic_set_null_on_delete(self, todo_item, topic):
        topic.delete()
        todo_item.refresh_from_db()
        assert todo_item.topic is None


class TestSubtask:
    def test_create_subtask(self, todo_item):
        subtask = Subtask.objects.create(
            todo_item=todo_item, name="Sub 1", position=0
        )
        assert subtask.is_completed is False
        assert str(subtask) == "Sub 1"

    def test_cascade_delete(self, todo_item):
        Subtask.objects.create(todo_item=todo_item, name="Sub 1")
        todo_item.delete()
        assert Subtask.objects.count() == 0

    def test_ordering(self, todo_item):
        Subtask.objects.create(todo_item=todo_item, name="Second", position=1)
        Subtask.objects.create(todo_item=todo_item, name="First", position=0)
        names = list(todo_item.subtasks.values_list("name", flat=True))
        assert names == ["First", "Second"]


class TestNote:
    def test_str(self, todo_item):
        note = Note.objects.create(todo_item=todo_item, content="A note")
        assert "Test Todo" in str(note)

    def test_ordering_newest_first(self, todo_item):
        Note.objects.create(todo_item=todo_item, content="First")
        Note.objects.create(todo_item=todo_item, content="Second")
        notes = list(todo_item.notes.values_list("content", flat=True))
        assert notes == ["Second", "First"]


class TestAttachment:
    def test_str(self, todo_item):
        att = Attachment(todo_item=todo_item, original_filename="doc.pdf")
        assert str(att) == "doc.pdf"


class TestActivityLog:
    def test_create_log(self, todo_item):
        log = ActivityLog.objects.create(
            todo_item=todo_item, action="created", detail="test"
        )
        assert "created" in str(log)

    def test_ordering_newest_first(self, todo_item):
        ActivityLog.objects.create(todo_item=todo_item, action="first")
        ActivityLog.objects.create(todo_item=todo_item, action="second")
        actions = list(todo_item.activity_logs.values_list("action", flat=True))
        assert actions == ["second", "first"]
