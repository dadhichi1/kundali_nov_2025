"""GraphQL router definitions for Kundali backend."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.schemas import AnalyticsSummary, ReportPayload, ReportSection
from backend.db import models

try:  # pragma: no cover - optional dependency
    import strawberry
    from strawberry.fastapi import GraphQLRouter
except ImportError:  # pragma: no cover - gracefully degrade when Strawberry missing
    strawberry = None  # type: ignore[assignment]
    GraphQLRouter = None  # type: ignore[misc]


def _build_graphql_router() -> Optional[APIRouter]:
    """Construct a GraphQL router when strawberry is installed."""

    if strawberry is None or GraphQLRouter is None:
        return None

    @strawberry.type
    class Chart:
        id: strawberry.ID
        chart_type: str
        generated_at: datetime

    @strawberry.type
    class ReportSectionType:
        title: str
        summary: Optional[str]
        content: str

    @strawberry.type
    class Report:
        id: strawberry.ID
        chart_id: strawberry.ID
        generated_at: datetime
        sections: list[ReportSectionType]

    @strawberry.type
    class Analytics:
        total_charts: int
        total_reports: int

    def get_session(info: strawberry.Info) -> Session:
        session: Session | None = info.context.get("session")
        if session is None:
            raise RuntimeError("Database session missing from GraphQL context")
        return session

    @strawberry.type
    class Query:
        @strawberry.field
        def chart(self, info: strawberry.Info, chart_id: strawberry.ID) -> Chart:
            session = get_session(info)
            chart = session.get(models.SavedChart, UUID(str(chart_id)))
            if chart is None:
                raise HTTPException(status_code=404, detail="Chart not found")
            return Chart(
                id=str(chart.id),
                chart_type=chart.chart_type,
                generated_at=chart.generated_at,
            )

        @strawberry.field
        def report(self, info: strawberry.Info, report_id: strawberry.ID) -> Report:
            session = get_session(info)
            chart = session.get(models.SavedChart, UUID(str(report_id)))
            if chart is None:
                raise HTTPException(status_code=404, detail="Report not found")
            payload = ReportPayload(
                id=chart.id,
                chart_id=chart.id,
                generated_at=chart.generated_at,
                sections=[
                    ReportSection(
                        title="Overview",
                        summary="Placeholder summary",
                        content="Narrative generated from persisted data.",
                    )
                ],
            )
            return Report(
                id=str(payload.id),
                chart_id=str(payload.chart_id),
                generated_at=payload.generated_at,
                sections=[
                    ReportSectionType(
                        title=section.title,
                        summary=section.summary,
                        content=section.content,
                    )
                    for section in payload.sections
                ],
            )

        @strawberry.field
        def analytics(self, info: strawberry.Info) -> Analytics:
            session = get_session(info)
            summary = AnalyticsSummary(
                total_charts=session.query(models.SavedChart).count(),
                total_reports=session.query(models.OrderHistory).count(),
                breakdowns=[],
            )
            return Analytics(
                total_charts=summary.total_charts,
                total_reports=summary.total_reports,
            )

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def generate_chart(
            self,
            info: strawberry.Info,
            full_name: str,
        ) -> Chart:
            session = get_session(info)
            chart = models.SavedChart(
                id=uuid4(),
                user_id=None,
                chart_type="natal",
                generated_at=datetime.utcnow(),
                input_payload={"full_name": full_name},
                chart_payload={},
            )
            session.add(chart)
            return Chart(id=str(chart.id), chart_type=chart.chart_type, generated_at=chart.generated_at)

    schema = strawberry.Schema(Query, Mutation)

    router = GraphQLRouter(
        schema,
        context_getter=lambda request: {"session": request.state.db},
    )
    return router  # type: ignore[return-value]


router = _build_graphql_router()

if router is None:
    # Provide a graceful fallback when Strawberry is not installed
    fallback_router = APIRouter(prefix="/graphql", tags=["GraphQL"])

    @fallback_router.get("", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    async def graphql_not_available() -> dict[str, str]:
        return {"detail": "GraphQL support is not available. Install strawberry-graphql."}

    router = fallback_router


__all__ = ["router"]
