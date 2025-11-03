"""FastAPI application wiring for Kundali backend."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from backend.api.middleware import ValidationErrorMiddleware
from backend.api.routes import graphql as graphql_routes
from backend.api.routes import rest as rest_routes

app = FastAPI(
    title="Kundali API",
    description=(
        "API for Kundali chart computation, narrative report delivery, and analytics. "
        "The service exposes REST and GraphQL interfaces for consumer applications."
    ),
    version="0.1.0",
    contact={"name": "Kundali Platform", "email": "support@kundali.example"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {"name": "Charts", "description": "Create and manage astrological charts."},
        {"name": "Reports", "description": "Access narrative astrology reports."},
        {"name": "Analytics", "description": "Usage metrics for business insights."},
        {"name": "GraphQL", "description": "GraphQL access to charting capabilities."},
    ],
)

app.add_middleware(ValidationErrorMiddleware)

app.include_router(rest_routes.router)
app.include_router(graphql_routes.router)


def custom_openapi() -> dict:
    """Generate OpenAPI schema with additional metadata."""

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
        tags=app.openapi_tags,
    )
    openapi_schema.setdefault("info", {}).setdefault("x-logo", {"url": "https://kundali.example/logo.png"})
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


__all__ = ["app"]
