from django.contrib import admin

from .models import ActivityLog, Attachment, Note, Subtask, TodoItem, Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 0


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0


@admin.register(TodoItem)
class TodoItemAdmin(admin.ModelAdmin):
    list_display = ["name", "state", "priority", "topic", "due_date", "owner"]
    list_filter = ["state", "priority", "topic"]
    search_fields = ["name", "description"]
    inlines = [SubtaskInline, NoteInline, AttachmentInline]


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ["todo_item", "action", "timestamp"]
    list_filter = ["action"]
