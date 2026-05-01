from django.urls import path

from . import views

app_name = "todos"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    path("today/", views.today_view, name="today"),
    # CRUD
    path("create/", views.todo_create, name="todo_create"),
    path("<uuid:pk>/", views.todo_detail, name="todo_detail"),
    path("<uuid:pk>/edit/", views.todo_edit, name="todo_edit"),
    path("<uuid:pk>/delete/", views.todo_delete, name="todo_delete"),
    path("<uuid:pk>/state/", views.todo_change_state, name="todo_change_state"),
    # Subtasks
    path("<uuid:pk>/subtask/add/", views.subtask_add, name="subtask_add"),
    path("subtask/<int:subtask_id>/toggle/", views.subtask_toggle, name="subtask_toggle"),
    path("subtask/<int:subtask_id>/delete/", views.subtask_delete, name="subtask_delete"),
    # Notes
    path("<uuid:pk>/note/add/", views.note_add, name="note_add"),
    path("note/<int:note_id>/delete/", views.note_delete, name="note_delete"),
    # Attachments
    path("<uuid:pk>/attachment/add/", views.attachment_add, name="attachment_add"),
    path(
        "attachment/<int:attachment_id>/delete/",
        views.attachment_delete,
        name="attachment_delete",
    ),
    # Reorder
    path("reorder/", views.todo_reorder, name="todo_reorder"),
    # Views
    path("kanban/", views.kanban_board, name="kanban"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("archive/", views.archive_view, name="archive"),
    # Topics
    path("topics/", views.topic_list, name="topic_list"),
    path("topics/create/", views.topic_create, name="topic_create"),
    path("topics/<int:pk>/delete/", views.topic_delete, name="topic_delete"),
    # Export
    path("export/<str:fmt>/", views.export_todos, name="export"),
]
