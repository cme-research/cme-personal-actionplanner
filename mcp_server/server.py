"""
MCP Server for Action Planner.

Exposes read/write access to todo items so Claude can manage them.
Run with: python -m mcp_server.server
"""

import os
import sys

import django

# Bootstrap Django before importing models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "actionplanner.settings")
django.setup()

from asgiref.sync import sync_to_async  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

from todos.models import ActivityLog, Subtask, TodoItem, Topic  # noqa: E402

mcp = FastMCP("ActionPlanner", instructions="Manage todo items in the Action Planner app.")


# Use the first superuser as default owner for MCP operations
def _get_owner():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(is_superuser=True).first()


@mcp.tool()
async def list_todos(
    state: str | None = None,
    topic: str | None = None,
    priority: str | None = None,
    include_archived: bool = False,
) -> list[dict]:
    """List todo items with optional filters.

    Args:
        state: Filter by state (new, current_work, finished, wont_do)
        topic: Filter by topic name
        priority: Filter by priority (low, medium, high, urgent)
        include_archived: Include finished/wont_do items (default False)
    """
    @sync_to_async
    def _impl():
        owner = _get_owner()
        if not owner:
            return [{"error": "No superuser found. Create one first."}]

        qs = TodoItem.objects.filter(owner=owner)
        if not include_archived:
            qs = qs.exclude(state__in=["finished", "wont_do"])
        if state:
            qs = qs.filter(state=state)
        if topic:
            qs = qs.filter(topic__name__iexact=topic)
        if priority:
            qs = qs.filter(priority=priority)

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "description": item.description,
                "due_date": str(item.due_date) if item.due_date else None,
                "priority": item.priority,
                "state": item.state,
                "topic": item.topic.name if item.topic else None,
                "item_type": item.item_type,
                "recurrence": item.recurrence,
                "estimation": str(item.estimation) if item.estimation else None,
                "is_overdue": item.is_overdue,
                "subtasks": [
                    {"name": s.name, "completed": s.is_completed}
                    for s in item.subtasks.all()
                ],
            }
            for item in qs
        ]

    return await _impl()


@mcp.tool()
async def get_todo(todo_id: str) -> dict:
    """Get a single todo item by ID.

    Args:
        todo_id: UUID of the todo item
    """
    @sync_to_async
    def _impl():
        owner = _get_owner()
        if not owner:
            return {"error": "No superuser found."}

        try:
            item = TodoItem.objects.get(pk=todo_id, owner=owner)
        except TodoItem.DoesNotExist:
            return {"error": f"Todo {todo_id} not found."}

        return {
            "id": str(item.id),
            "name": item.name,
            "description": item.description,
            "due_date": str(item.due_date) if item.due_date else None,
            "priority": item.priority,
            "state": item.state,
            "topic": item.topic.name if item.topic else None,
            "item_type": item.item_type,
            "recurrence": item.recurrence,
            "estimation": str(item.estimation) if item.estimation else None,
            "is_overdue": item.is_overdue,
            "notes": [
                {"content": n.content, "created_at": n.created_at.isoformat()}
                for n in item.notes.all()
            ],
            "subtasks": [
                {"id": s.id, "name": s.name, "completed": s.is_completed}
                for s in item.subtasks.all()
            ],
            "activity_log": [
                {"action": log.action, "detail": log.detail, "timestamp": log.timestamp.isoformat()}
                for log in item.activity_logs.all()[:10]
            ],
        }

    return await _impl()


@mcp.tool()
async def create_todo(
    name: str,
    description: str = "",
    due_date: str | None = None,
    priority: str = "medium",
    topic: str | None = None,
    item_type: str = "",
    recurrence: str = "none",
    estimation: str | None = None,
) -> dict:
    """Create a new todo item.

    Args:
        name: Title of the todo
        description: Detailed description
        due_date: Due date in YYYY-MM-DD format
        priority: low, medium, high, or urgent
        topic: Topic name (will be created if it doesn't exist)
        item_type: Free-form type label
        recurrence: none, daily, weekly, or monthly
        estimation: Estimated effort as HH:MM:SS (e.g. 2:30:00)
    """
    @sync_to_async
    def _impl():
        import datetime

        owner = _get_owner()
        if not owner:
            return {"error": "No superuser found."}

        topic_obj = None
        if topic:
            topic_obj, _ = Topic.objects.get_or_create(name=topic)

        parsed_date = None
        if due_date:
            try:
                parsed_date = datetime.date.fromisoformat(due_date)
            except ValueError:
                return {"error": f"Invalid date format: {due_date}. Use YYYY-MM-DD."}

        parsed_estimation = None
        if estimation:
            try:
                parts = estimation.split(":")
                secs = int(parts[2]) if len(parts) > 2 else 0
                parsed_estimation = datetime.timedelta(
                    hours=int(parts[0]), minutes=int(parts[1]), seconds=secs
                )
            except (ValueError, IndexError):
                return {"error": f"Invalid estimation format: {estimation}. Use HH:MM or HH:MM:SS."}

        item = TodoItem.objects.create(
            name=name,
            description=description,
            due_date=parsed_date,
            priority=priority,
            topic=topic_obj,
            item_type=item_type,
            recurrence=recurrence,
            estimation=parsed_estimation,
            owner=owner,
        )
        ActivityLog.objects.create(todo_item=item, action="created", detail="Created via MCP")
        return {"id": str(item.id), "name": item.name, "status": "created"}

    return await _impl()


@mcp.tool()
async def update_todo(
    todo_id: str,
    name: str | None = None,
    description: str | None = None,
    due_date: str | None = None,
    priority: str | None = None,
    state: str | None = None,
    topic: str | None = None,
    item_type: str | None = None,
    estimation: str | None = None,
) -> dict:
    """Update an existing todo item. Only provided fields are changed.

    Args:
        todo_id: UUID of the todo item
        name: New title
        description: New description
        due_date: New due date (YYYY-MM-DD) or empty string to clear
        priority: New priority (low, medium, high, urgent)
        state: New state (new, current_work, finished, wont_do)
        topic: New topic name
        item_type: New type label
        estimation: Estimated effort as HH:MM:SS, or empty string to clear
    """
    @sync_to_async
    def _impl():
        import datetime

        owner = _get_owner()
        if not owner:
            return {"error": "No superuser found."}

        try:
            item = TodoItem.objects.get(pk=todo_id, owner=owner)
        except TodoItem.DoesNotExist:
            return {"error": f"Todo {todo_id} not found."}

        changes = []
        if name is not None:
            item.name = name
            changes.append("name")
        if description is not None:
            item.description = description
            changes.append("description")
        if due_date is not None:
            if due_date == "":
                item.due_date = None
            else:
                try:
                    item.due_date = datetime.date.fromisoformat(due_date)
                except ValueError:
                    return {"error": f"Invalid date: {due_date}"}
            changes.append("due_date")
        if priority is not None:
            item.priority = priority
            changes.append("priority")
        if state is not None:
            old_state = item.state
            item.state = state
            changes.append(f"state: {old_state} -> {state}")
        if topic is not None:
            topic_obj, _ = Topic.objects.get_or_create(name=topic)
            item.topic = topic_obj
            changes.append("topic")
        if item_type is not None:
            item.item_type = item_type
            changes.append("item_type")
        if estimation is not None:
            if estimation == "":
                item.estimation = None
            else:
                try:
                    parts = estimation.split(":")
                    item.estimation = datetime.timedelta(
                        hours=int(parts[0]), minutes=int(parts[1]),
                        seconds=int(parts[2]) if len(parts) > 2 else 0,
                    )
                except (ValueError, IndexError):
                    return {"error": f"Invalid estimation: {estimation}. Use HH:MM or HH:MM:SS."}
            changes.append("estimation")

        item.save()
        ActivityLog.objects.create(
            todo_item=item, action="updated", detail=f"Via MCP: {', '.join(changes)}"
        )
        return {"id": str(item.id), "name": item.name, "status": "updated", "changes": changes}

    return await _impl()


@mcp.tool()
async def delete_todo(todo_id: str) -> dict:
    """Delete a todo item.

    Args:
        todo_id: UUID of the todo item to delete
    """
    @sync_to_async
    def _impl():
        owner = _get_owner()
        if not owner:
            return {"error": "No superuser found."}

        try:
            item = TodoItem.objects.get(pk=todo_id, owner=owner)
        except TodoItem.DoesNotExist:
            return {"error": f"Todo {todo_id} not found."}

        name = item.name
        item.delete()
        return {"name": name, "status": "deleted"}

    return await _impl()


@mcp.tool()
async def add_note(todo_id: str, content: str) -> dict:
    """Add a note to a todo item.

    Args:
        todo_id: UUID of the todo item
        content: Note text
    """
    @sync_to_async
    def _impl():
        from todos.models import Note

        owner = _get_owner()
        if not owner:
            return {"error": "No superuser found."}

        try:
            item = TodoItem.objects.get(pk=todo_id, owner=owner)
        except TodoItem.DoesNotExist:
            return {"error": f"Todo {todo_id} not found."}

        note = Note.objects.create(todo_item=item, content=content)
        ActivityLog.objects.create(todo_item=item, action="note_added", detail="Via MCP")
        return {"note_id": note.id, "status": "added"}

    return await _impl()


@mcp.tool()
async def add_subtask(todo_id: str, name: str) -> dict:
    """Add a subtask to a todo item.

    Args:
        todo_id: UUID of the todo item
        name: Subtask name
    """
    @sync_to_async
    def _impl():
        owner = _get_owner()
        if not owner:
            return {"error": "No superuser found."}

        try:
            item = TodoItem.objects.get(pk=todo_id, owner=owner)
        except TodoItem.DoesNotExist:
            return {"error": f"Todo {todo_id} not found."}

        subtask = Subtask.objects.create(
            todo_item=item, name=name, position=item.subtasks.count()
        )
        ActivityLog.objects.create(todo_item=item, action="subtask_added", detail=f"Via MCP: {name}")
        return {"subtask_id": subtask.id, "status": "added"}

    return await _impl()


@mcp.tool()
async def list_topics() -> list[dict]:
    """List all available topics."""
    @sync_to_async
    def _impl():
        return [
            {"id": t.id, "name": t.name, "item_count": t.items.count()}
            for t in Topic.objects.all()
        ]

    return await _impl()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run()
