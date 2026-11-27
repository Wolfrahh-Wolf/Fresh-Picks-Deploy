# Python Backend

Covers Flask 3.1 and FastAPI 0.115 application structure, dependency handling, WSGI/ASGI configuration, request validation and async pitfalls; versions checked 2026-11-26. The project's `pyproject.toml` or `requirements.txt` and lockfile win over any version here.

## Contents

- Choosing Flask vs. FastAPI
- Flask: application factory, blueprints, configuration
- FastAPI: project layout, lifespan, dependency injection, Pydantic validation
- WSGI and ASGI servers
- Async pitfalls
- Validation

## Guidance

### Choosing Flask vs. FastAPI

| Criterion | Flask 3.1 (WSGI/async) | FastAPI 0.115 (ASGI) |
|---|---|---|
| Concurrency model | Threaded workers (Gunicorn); limited async support | Full async via Uvicorn/Hypercorn; native `async def` |
| Validation | Manual or Marshmallow/Pydantic add-ons | Built-in Pydantic v2 |
| Auto-generated docs | Third-party (flask-smorest, flasgger) | Built-in OpenAPI at `/docs` |
| Ecosystem maturity | Large; many extensions | Smaller; growing fast |
| When to prefer | Existing Flask codebase; synchronous workloads | New greenfield API; heavy async I/O; auto-docs required |

Match the existing project's framework; do not introduce a second one.

### Flask: application factory, blueprints, configuration

Always use the **application factory** pattern. A module-level `app = Flask(__name__)` causes circular imports and makes testing hard.

```python
# app/__init__.py
from flask import Flask
from app.config import config_by_name
from app.api.users import users_bp
from app.extensions import db

def create_app(config_name: str = "production") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    db.init_app(app)
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    return app
```

```python
# app/config.py
import os

class Config:
    SECRET_KEY    = os.environ["SECRET_KEY"]   # crash early if missing
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG         = False
    DATABASE_URL  = os.environ["DATABASE_URL"]

class DevelopmentConfig(Config):
    DEBUG         = True
    DATABASE_URL  = os.getenv("DATABASE_URL", "sqlite:///dev.db")

config_by_name = {"production": ProductionConfig, "development": DevelopmentConfig}
```

**Blueprint layout:**

```
app/
  __init__.py      # create_app factory
  config.py
  extensions.py    # db, migrate, login_manager singletons
  api/
    users.py       # Blueprint("users", ...)
  services/
    user_service.py
  models/
    user.py
wsgi.py            # production entry point: app = create_app("production")
```

The WSGI entry point for Gunicorn: `gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app`. Never use `flask run` or `app.run()` in production.

### FastAPI: project layout, lifespan, dependency injection, Pydantic validation

**Layout:**

```
src/
  main.py          # FastAPI(lifespan=lifespan); include routers
  core/
    config.py      # pydantic-settings BaseSettings
    database.py    # async engine, sessionmaker
  users/
    router.py
    schemas.py     # Pydantic request/response models
    models.py      # SQLAlchemy ORM
    services.py
    dependencies.py
```

**Lifespan** (FastAPI 0.95+ preferred over `@app.on_event`, which is deprecated):

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()   # startup
    yield
    await database.disconnect() # shutdown

app = FastAPI(lifespan=lifespan)
```

**Dependency injection for DB sessions:**

```python
async def get_db():
    async with async_session_maker() as session:
        yield session          # session closed even if handler raises

@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_service.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**Configuration with pydantic-settings:**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    secret_key:   str
    debug:        bool = False
    model_config  = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### WSGI and ASGI servers

| Framework | Protocol | Recommended server | Production command |
|---|---|---|---|
| Flask | WSGI | Gunicorn | `gunicorn -w 4 wsgi:app` |
| FastAPI | ASGI | Uvicorn | `uvicorn src.main:app --workers 4 --host 0.0.0.0` |

For multi-core FastAPI, use multiple Uvicorn worker processes (`--workers`), not multiple async tasks in one process. With Docker/Kubernetes, run one worker per container and scale horizontally.

For Flask with async views (Flask 3.x supports `async def` views via `asgiref`), serve through an ASGI adapter or stick to WSGI for predictability.

### Async pitfalls

| Mistake | Effect | Fix |
|---|---|---|
| `requests.get()` inside `async def` | Blocks the event loop for the duration of the HTTP call | Use `httpx.AsyncClient` or `aiohttp` |
| Synchronous ORM calls (SQLAlchemy non-async) inside `async def` | Blocks the event loop | Use SQLAlchemy 2.0 `AsyncSession` with `asyncpg` |
| CPU-bound code in an async endpoint | Stalls all concurrent requests | Offload to a thread (`asyncio.run_in_executor`) or a task queue |
| `async def` endpoint with no `await` | FastAPI/Starlette runs it on the event loop, blocking it if it is slow | Use plain `def` for synchronous endpoints; FastAPI dispatches them to a threadpool |
| Not closing async resources in lifespan | Connection leaks on restart | Always use `yield` in lifespan and clean up after it |

**FastAPI sync vs. async rule:** use `async def` only when the function awaits something. Plain `def` endpoints run in a thread pool and do not block the event loop.

### Validation

Flask: validate every inbound payload explicitly. Marshmallow or Pydantic (with `flask-pydantic`) are common. At minimum check required fields, types and value ranges before passing data to the service layer.

FastAPI: declare Pydantic models for every request body and response. Validation is automatic at the boundary. Use `model_config = ConfigDict(extra='forbid')` to reject unexpected fields:

```python
from pydantic import BaseModel, ConfigDict, Field

class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: str = Field(min_length=3, max_length=64)
    email:    str = Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(min_length=12)
```

## Examples

### Flask Blueprint with error handling

```python
# app/api/users.py
from flask import Blueprint, jsonify, request, abort
from app.services.user_service import get_user_by_id, create_user
from app.schemas.user_schema import CreateUserSchema

users_bp = Blueprint("users", __name__)
schema   = CreateUserSchema()

@users_bp.get("/<int:user_id>")
def get_user(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        abort(404, "User not found")
    return jsonify(user.to_dict())

@users_bp.post("/")
def create():
    errors = schema.validate(request.json or {})
    if errors:
        abort(400, errors)
    user = create_user(request.json)
    return jsonify(user.to_dict()), 201
```

### FastAPI router with dependency injection

```python
# users/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import CreateUserRequest, UserResponse
from .services import get_user, create_user
from core.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse, status_code=201)
async def create(body: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    return await create_user(db, body)
```

## Common mistakes

| Mistake | Why it hurts | Do instead |
|---|---|---|
| Module-level `app = Flask(__name__)` | Circular imports; untestable | Use application factory with `create_app()` |
| `flask run` in production | Single-threaded dev server; no restart on crash | Use Gunicorn with multiple workers |
| Synchronous I/O in FastAPI `async def` | Blocks the event loop | Use async libraries or run sync code in a thread executor |
| Skipping `extra='forbid'` on Pydantic models | Silently accepts unexpected fields; allows mass assignment | Set `ConfigDict(extra='forbid')` on all request models |
| Using `@app.on_event` in FastAPI | Deprecated since 0.95; removed in future versions | Use `lifespan` context manager |
| Reading `os.environ.get("KEY")` without a default for required vars | Returns `None`; fails later with an obscure error | Use `os.environ["KEY"]` or `pydantic-settings` with no default |

## Checklist

- [ ] Flask apps use application factory (`create_app`); no module-level app instance.
- [ ] All configuration loaded from environment variables; no hardcoded secrets.
- [ ] Production deployment uses Gunicorn (Flask) or Uvicorn (FastAPI), not the dev server.
- [ ] FastAPI endpoints use `async def` only when they `await`; synchronous endpoints use plain `def`.
- [ ] No synchronous I/O library (e.g., `requests`) called inside an `async def` route.
- [ ] FastAPI lifespan used for startup/shutdown resource management.
- [ ] All request bodies validated via Pydantic (FastAPI) or Marshmallow/equivalent (Flask).
- [ ] `extra='forbid'` set on FastAPI request models.
- [ ] DB sessions opened and closed within a dependency `yield`; not managed inside handlers.

## Verify with context7 and gh_grep

- **context7:** Resolve `flask` and `fastapi` at their locked versions. Check: Flask 3 async view support and ASGI adapter; FastAPI `lifespan` parameter availability (0.95+); `pydantic-settings` `BaseSettings` for Pydantic v2; SQLAlchemy 2.0 `AsyncSession` API.
- **gh_grep:** Search `create_app(` for Flask factory patterns; `@asynccontextmanager` with `lifespan` for FastAPI startup; `async with async_session_maker()` for SQLAlchemy async session patterns; `ConfigDict(extra='forbid')` for Pydantic model hardening.

## Sources

- Flask 3.1 application factories: https://flask.palletsprojects.com/en/3.1.x/patterns/appfactories/
- Flask 3.1 blueprints: https://flask.palletsprojects.com/en/3.1.x/blueprints/
- FastAPI 0.115 lifespan: https://fastapi.tiangolo.com/advanced/events/
- FastAPI 0.115 dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
- FastAPI async vs. sync: https://fastapi.tiangolo.com/async/
- pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Uvicorn deployment: https://www.uvicorn.org/deployment/
