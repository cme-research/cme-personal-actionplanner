import datetime
import uuid

from django.conf import settings
from django.db import models


class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TodoItem(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class State(models.TextChoices):
        NEW = "new", "New"
        CURRENT_WORK = "current_work", "Current Work"
        FINISHED = "finished", "Finished"
        WONT_DO = "wont_do", "Won't Do"

    class RecurrenceInterval(models.TextChoices):
        NONE = "none", "None"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    item_type = models.CharField(max_length=100, blank=True, default="")
    topic = models.ForeignKey(
        Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name="items"
    )
    state = models.CharField(
        max_length=15, choices=State.choices, default=State.NEW
    )
    position = models.IntegerField(default=0)
    recurrence = models.CharField(
        max_length=10,
        choices=RecurrenceInterval.choices,
        default=RecurrenceInterval.NONE,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="todo_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "-priority", "due_date"]

    def __str__(self):
        return self.name

    @property
    def is_overdue(self):
        if self.due_date and self.state not in (self.State.FINISHED, self.State.WONT_DO):
            return self.due_date < datetime.date.today()
        return False

    @property
    def is_due_today(self):
        if self.due_date:
            return self.due_date == datetime.date.today()
        return False

    @property
    def is_due_this_week(self):
        if self.due_date:
            today = datetime.date.today()
            end_of_week = today + datetime.timedelta(days=(6 - today.weekday()))
            return today <= self.due_date <= end_of_week
        return False


class Subtask(models.Model):
    todo_item = models.ForeignKey(
        TodoItem, on_delete=models.CASCADE, related_name="subtasks"
    )
    name = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.name


class Note(models.Model):
    todo_item = models.ForeignKey(
        TodoItem, on_delete=models.CASCADE, related_name="notes"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.todo_item.name} at {self.created_at}"


class Attachment(models.Model):
    todo_item = models.ForeignKey(
        TodoItem, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="attachments/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename


class ActivityLog(models.Model):
    todo_item = models.ForeignKey(
        TodoItem, on_delete=models.CASCADE, related_name="activity_logs"
    )
    action = models.CharField(max_length=50)
    detail = models.TextField(blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} on {self.todo_item.name}"
