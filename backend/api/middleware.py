"""Custom FastAPI middleware utilities."""
from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from backend.db.database import get_session_factory


class ValidationErrorMiddleware(BaseHTTPMiddleware):
    """Format FastAPI validation errors in a consistent envelope."""

    async def dispatch(  # type: ignore[override]
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        session_factory = get_session_factory()
        request.state.db = session_factory()  # type: ignore[attr-defined]
        db_session = request.state.db  # type: ignore[attr-defined]
        try:
            response = await call_next(request)
        except RequestValidationError as exc:  # pragma: no cover - relies on runtime validation
            db_session.rollback()
            return JSONResponse(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": exc.errors(), "message": "Invalid request payload"},
            )
        except Exception:
            db_session.rollback()
            raise
        else:
            if db_session.is_active and (
                db_session.dirty or db_session.new or db_session.deleted
            ):
                db_session.commit()
            return response
        finally:
            db_session.close()
