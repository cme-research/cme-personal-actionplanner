import calendar as cal
import csv
import json
from datetime import date, timedelta
from io import StringIO

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    AttachmentForm,
    NoteForm,
    SearchForm,
    SubtaskForm,
    TodoItemForm,
    TopicForm,
)
from .models import ActivityLog, Attachment, Note, Subtask, TodoItem, Topic


def _log_activity(item, action, detail=""):
    ActivityLog.objects.create(todo_item=item, action=action, detail=detail)


# --- Dashboard ---


def dashboard(request):
    items = TodoItem.objects.filter(owner=request.user).exclude(
        state__in=[TodoItem.State.FINISHED, TodoItem.State.WONT_DO]
    )
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        items = _apply_filters(items, search_form.cleaned_data)

    today = date.today()
    overdue = items.filter(due_date__lt=today)
    due_today = items.filter(due_date=today)
    upcoming = items.filter(
        due_date__gt=today, due_date__lte=today + timedelta(days=7)
    )

    context = {
        "items": items,
        "search_form": search_form,
        "overdue_count": overdue.count(),
        "due_today_count": due_today.count(),
        "upcoming_count": upcoming.count(),
        "topics": Topic.objects.all(),
    }
    return render(request, "todos/dashboard.html", context)


# --- CRUD ---


def todo_create(request):
    if request.method == "POST":
        form = TodoItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            _log_activity(item, "created")
            messages.success(request, f'Todo "{item.name}" created.')
            return redirect("todos:todo_detail", pk=item.pk)
    else:
        form = TodoItemForm()
    return render(request, "todos/todo_form.html", {"form": form, "title": "New Todo"})


def todo_detail(request, pk):
    item = get_object_or_404(TodoItem, pk=pk, owner=request.user)
    subtask_form = SubtaskForm()
    note_form = NoteForm()
    attachment_form = AttachmentForm()
    context = {
        "item": item,
        "subtask_form": subtask_form,
        "note_form": note_form,
        "attachment_form": attachment_form,
        "activity_logs": item.activity_logs.all()[:20],
    }
    return render(request, "todos/todo_detail.html", context)


def todo_edit(request, pk):
    item = get_object_or_404(TodoItem, pk=pk, owner=request.user)
    old_state = item.state
    if request.method == "POST":
        form = TodoItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            if old_state != item.state:
                _log_activity(
                    item, "state_changed", f"{old_state} -> {item.state}"
                )
            _log_activity(item, "edited")
            messages.success(request, f'Todo "{item.name}" updated.')
            return redirect("todos:todo_detail", pk=item.pk)
    else:
        form = TodoItemForm(instance=item)
    return render(
        request, "todos/todo_form.html", {"form": form, "title": "Edit Todo", "item": item}
    )


@require_POST
def todo_delete(request, pk):
    item = get_object_or_404(TodoItem, pk=pk, owner=request.user)
    name = item.name
    item.delete()
    messages.success(request, f'Todo "{name}" deleted.')
    return redirect("todos:dashboard")


@require_POST
def todo_change_state(request, pk):
    item = get_object_or_404(TodoItem, pk=pk, owner=request.user)
    new_state = request.POST.get("state")
    if new_state in dict(TodoItem.State.choices):
        old_state = item.state
        item.state = new_state
        item.save(update_fields=["state", "updated_at"])
        _log_activity(item, "state_changed", f"{old_state} -> {new_state}")

        # Handle recurrence: create next item when finishing a recurring todo
        if (
            new_state == TodoItem.State.FINISHED
            and item.recurrence != TodoItem.RecurrenceInterval.NONE
            and item.due_date
        ):
            _create_next_recurring(item)

    return redirect(request.POST.get("next", "todos:dashboard"))


def _create_next_recurring(item):
    if item.recurrence == TodoItem.RecurrenceInterval.DAILY:
        delta = timedelta(days=1)
    elif item.recurrence == TodoItem.RecurrenceInterval.WEEKLY:
        delta = timedelta(weeks=1)
    elif item.recurrence == TodoItem.RecurrenceInterval.MONTHLY:
        delta = timedelta(days=30)
    else:
        return

    new_item = TodoItem.objects.create(
        name=item.name,
        description=item.description,
        due_date=item.due_date + delta,
        priority=item.priority,
        item_type=item.item_type,
        topic=item.topic,
        state=TodoItem.State.NEW,
        recurrence=item.recurrence,
        owner=item.owner,
    )
    _log_activity(new_item, "created", "Auto-created from recurring todo")


# --- Subtasks ---


@require_POST
def subtask_add(request, pk):
    item = get_object_or_404(TodoItem, pk=pk, owner=request.user)
    form = SubtaskForm(request.POST)
    if form.is_valid():
        subtask = form.save(commit=False)
        subtask.todo_item = item
        subtask.position = item.subtasks.count()
        subtask.save()
        _log_activity(item, "subtask_added", subtask.name)
    return redirect("todos:todo_detail", pk=pk)


@require_POST
def subtask_toggle(request, subtask_id):
    subtask = get_object_or_404(Subtask, id=subtask_id, todo_item__owner=request.user)
    subtask.is_completed = not subtask.is_completed
    subtask.save(update_fields=["is_completed"])
    _log_activity(
        subtask.todo_item,
        "subtask_toggled",
        f"{subtask.name}: {'completed' if subtask.is_completed else 'uncompleted'}",
    )
    return redirect("todos:todo_detail", pk=subtask.todo_item.pk)


@require_POST
def subtask_delete(request, subtask_id):
    subtask = get_object_or_404(Subtask, id=subtask_id, todo_item__owner=request.user)
    pk = subtask.todo_item.pk
    _log_activity(subtask.todo_item, "subtask_deleted", subtask.name)
    subtask.delete()
    return redirect("todos:todo_detail", pk=pk)


# --- Notes ---


@require_POST
def note_add(request, pk):
    item = get_object_or_404(TodoItem, pk=pk, owner=request.user)
    form = NoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.todo_item = item
        note.save()
        _log_activity(item, "note_added")
    return redirect("todos:todo_detail", pk=pk)


@require_POST
def note_delete(request, note_id):
    note = get_object_or_404(Note, id=note_id, todo_item__owner=request.user)
    pk = note.todo_item.pk
    _log_activity(note.todo_item, "note_deleted")
    note.delete()
    return redirect("todos:todo_detail", pk=pk)


# --- Attachments ---


@require_POST
def attachment_add(request, pk):
    item = get_object_or_404(TodoItem, pk=pk, owner=request.user)
    form = AttachmentForm(request.POST, request.FILES)
    if form.is_valid():
        attachment = form.save(commit=False)
        attachment.todo_item = item
        attachment.original_filename = request.FILES["file"].name
        attachment.save()
        _log_activity(item, "attachment_added", attachment.original_filename)
    return redirect("todos:todo_detail", pk=pk)


@require_POST
def attachment_delete(request, attachment_id):
    attachment = get_object_or_404(
        Attachment, id=attachment_id, todo_item__owner=request.user
    )
    pk = attachment.todo_item.pk
    _log_activity(attachment.todo_item, "attachment_deleted", attachment.original_filename)
    attachment.file.delete()
    attachment.delete()
    return redirect("todos:todo_detail", pk=pk)


# --- Reorder ---


@require_POST
def todo_reorder(request):
    try:
        order = json.loads(request.body)
        for i, item_id in enumerate(order.get("items", [])):
            TodoItem.objects.filter(pk=item_id, owner=request.user).update(position=i)
        return JsonResponse({"status": "ok"})
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"status": "error"}, status=400)


# --- Kanban ---


def kanban_board(request):
    active = TodoItem.objects.filter(owner=request.user).exclude(
        state__in=[TodoItem.State.FINISHED, TodoItem.State.WONT_DO]
    )
    done = (
        TodoItem.objects.filter(owner=request.user, state=TodoItem.State.FINISHED)
        .order_by("-updated_at")[:10]
    )
    columns = {
        TodoItem.State.NEW: active.filter(state=TodoItem.State.NEW),
        TodoItem.State.CURRENT_WORK: active.filter(state=TodoItem.State.CURRENT_WORK),
        TodoItem.State.FINISHED: done,
    }
    return render(request, "todos/kanban.html", {"columns": columns})


# --- Calendar ---


def calendar_view(request):
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    month_cal = cal.monthcalendar(year, month)
    items = TodoItem.objects.filter(
        owner=request.user,
        due_date__year=year,
        due_date__month=month,
    ).exclude(state__in=[TodoItem.State.FINISHED, TodoItem.State.WONT_DO])

    items_by_day = {}
    for item in items:
        day = item.due_date.day
        items_by_day.setdefault(day, []).append(item)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        "month_cal": month_cal,
        "items_by_day": items_by_day,
        "year": year,
        "month": month,
        "month_name": cal.month_name[month],
        "today": today,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }
    return render(request, "todos/calendar.html", context)


# --- Archive ---


def archive_view(request):
    items = TodoItem.objects.filter(
        owner=request.user,
        state__in=[TodoItem.State.FINISHED, TodoItem.State.WONT_DO],
    )
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        items = _apply_filters(items, search_form.cleaned_data)
    return render(
        request, "todos/archive.html", {"items": items, "search_form": search_form}
    )


# --- Topics ---


def topic_list(request):
    topics = Topic.objects.all()
    form = TopicForm()
    return render(request, "todos/topic_list.html", {"topics": topics, "form": form})


@require_POST
def topic_create(request):
    form = TopicForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f'Topic "{form.cleaned_data["name"]}" created.')
    return redirect("todos:topic_list")


@require_POST
def topic_delete(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    name = topic.name
    topic.delete()
    messages.success(request, f'Topic "{name}" deleted.')
    return redirect("todos:topic_list")


# --- Export ---


def export_todos(request, fmt):
    items = TodoItem.objects.filter(owner=request.user)

    if fmt == "json":
        data = []
        for item in items:
            data.append(
                {
                    "id": str(item.id),
                    "name": item.name,
                    "description": item.description,
                    "due_date": str(item.due_date) if item.due_date else None,
                    "priority": item.priority,
                    "item_type": item.item_type,
                    "topic": item.topic.name if item.topic else None,
                    "state": item.state,
                    "recurrence": item.recurrence,
                    "estimation": str(item.estimation) if item.estimation else None,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                }
            )
        response = HttpResponse(
            json.dumps(data, indent=2), content_type="application/json"
        )
        response["Content-Disposition"] = 'attachment; filename="todos.json"'
        return response

    elif fmt == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "name",
                "description",
                "due_date",
                "priority",
                "item_type",
                "topic",
                "state",
                "recurrence",
                "estimation",
                "created_at",
                "updated_at",
            ]
        )
        for item in items:
            writer.writerow(
                [
                    str(item.id),
                    item.name,
                    item.description,
                    item.due_date,
                    item.priority,
                    item.item_type,
                    item.topic.name if item.topic else "",
                    item.state,
                    item.recurrence,
                    str(item.estimation) if item.estimation else "",
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                ]
            )
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="todos.csv"'
        return response

    return HttpResponse("Invalid format. Use 'json' or 'csv'.", status=400)


# --- Helpers ---


def _apply_filters(queryset, data):
    q = data.get("q")
    if q:
        queryset = queryset.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if data.get("topic"):
        queryset = queryset.filter(topic=data["topic"])
    if data.get("state"):
        queryset = queryset.filter(state=data["state"])
    if data.get("priority"):
        queryset = queryset.filter(priority=data["priority"])
    if data.get("date_from"):
        queryset = queryset.filter(due_date__gte=data["date_from"])
    if data.get("date_to"):
        queryset = queryset.filter(due_date__lte=data["date_to"])
    return queryset
