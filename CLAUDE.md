# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered personal todo and organizer web application. Built with Python/Django, deployed via Docker Compose with Gunicorn on an Ubuntu 24 VPS. Publicly accessible from the internet — security is a top priority.

## Tech Stack

- **Language**: Python
- **Framework**: Django (templates for UI, no SPA framework)
- **Database**: SQLite (lightweight, file-based)
- **WSGI Server**: Gunicorn
- **Containerization**: Docker Compose
- **Linting/Formatting**: Ruff
- **Type Checking**: mypy
- **Testing**: pytest (with pytest-django)
- **MCP Server**: FastMCP or similar, exposing read/write access to todo items for Claude

## Deployment

- Runs on a personal VPS (Ubuntu Linux 24)
- Docker Compose orchestrates the app (Gunicorn + Django)
- Accessible from the internet — all endpoints behind authentication
- Static files served via WhiteNoise or nginx

## Security Requirements

- State-of-the-art Django security: CSRF, session management, secure cookies, HSTS
- Login required for all views; use Django's built-in auth system
- Content Security Policy headers
- Rate limiting on login
- DEBUG=False in production, SECRET_KEY from environment
- ALLOWED_HOSTS properly configured

## UI Requirements

- Clean, modern Django templates (no JS framework)
- Fully responsive — must work well on phone screens (Chrome, Firefox)
- Plain, good-looking design using a CSS framework (e.g., Bootstrap 5 or similar)

## Data Model

### TodoItem
- `name`: short title (CharField)
- `description`: detailed text (TextField)
- `due_date`: target date (DateField)
- `priority`: e.g., low/medium/high/urgent (CharField with choices)
- `item_type`: free-form or predefined type (CharField)
- `topic`: category — house, business, personal, gardening, and user-extensible (ForeignKey to Topic)
- `state`: new | current_work | finished | wont_do (CharField with choices)
- `created_at`, `updated_at`: timestamps

### Topic
- `name`: category name (CharField, unique)
- Default topics: house, business, personal, gardening

## Additional Features

### Organization & Planning
- **Subtasks/checklists**: break a todo into smaller steps with individual completion tracking
- **Recurring todos**: daily/weekly/monthly repeating items (e.g., "water plants every Sunday")
- **Due date reminders**: visual indicators for overdue, due today, due this week
- **Calendar view**: see todos on a monthly/weekly calendar alongside the list view

### Productivity
- **Notes/comments per item**: append timestamped notes to track progress on a todo
- **File attachments**: attach images or documents to a todo (e.g., a receipt, a sketch)
- **Search & filter**: full-text search across items, filter by topic/state/priority/date range
- **Drag-and-drop reordering**: manual sort within a topic or priority group
- **Kanban board view**: columns for new → current_work → finished (visual workflow)

### AI Features (via MCP/Claude)
- **Smart suggestions**: Claude proposes next steps, breaks down vague items, or suggests priorities
- **Natural language input**: type "buy groceries tomorrow high priority" and Claude parses it into a structured todo
- **Daily digest/summary**: Claude generates a briefing of what's due, overdue, and in progress

### Quality of Life
- **Archive view**: finished/wont_do items move out of the main view but remain searchable
- **Dark mode**: toggle or auto-detect based on system preference
- **Export**: download todos as CSV/JSON for backup
- **Activity log**: history of state changes per item (when was it created, started, completed)

## MCP Server

An MCP (Model Context Protocol) server exposes the todo API so Claude can read and write items programmatically. Runs as a separate process using FastMCP.

```bash
# Run MCP server (stdio transport)
python -m mcp_server.server
```

Tools: `list_todos`, `get_todo`, `create_todo`, `update_todo`, `delete_todo`, `add_note`, `add_subtask`, `list_topics`. Operates as the first superuser.

## Git Workflow

- **Main branch**: `main` (protected, stable)
- **Development**: push to `dev` branch, merge to `main` via PR
- **GitHub org**: `cme-research`, use `gh` CLI for repo access
- Never force-push to `main`

## Build & Run Commands

```bash
# Development
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests (PYTHONPATH="" isolates from ROS system packages)
PYTHONPATH="" python -m pytest
PYTHONPATH="" python -m pytest todos/tests/test_models.py  # single file
PYTHONPATH="" python -m pytest -k "test_name"               # single test

# Seed default topics
python manage.py seed_topics

# Lint & format
ruff check .
ruff format .

# Type check
mypy .

# Production (Docker)
docker compose up --build
docker compose down
```

## Project Structure (target)

```
cme-personal-actionplanner/
├── actionplanner/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── todos/                  # Main app: models, views, templates
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── templates/todos/
│   └── tests/
├── mcp_server/             # MCP server for Claude integration
├── templates/              # Base templates
├── static/                 # CSS, JS, images
├── Dockerfile
├── docker-compose.yml
├── gunicorn.conf.py
├── manage.py
├── pyproject.toml
└── requirements.txt
```
