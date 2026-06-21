Backend

FastAPI backend for session management, WebSocket manager, authentication, and ML worker integration.

Planned structure:
- `app/` - application package
  - `api/` - REST endpoints
  - `core/` - configs, security
  - `db/` - models, migrations
  - `services/` - domain services
  - `workers/` - Celery tasks

Use `pyproject.toml` or `poetry` for dependency management.
