"""Pydantic schemas for Kundali API."""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator


class BirthLocation(BaseModel):
    """Geographical information for birth location."""

    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    city: Optional[str] = Field(None, description="City of birth")
    state: Optional[str] = Field(None, description="State or region of birth")
    country: Optional[str] = Field(None, description="Country of birth")


class BirthDataInput(BaseModel):
    """Payload submitted by users requesting a chart computation."""

    full_name: str = Field(..., min_length=1, description="Full name of the individual")
    birth_date: date = Field(..., description="Date of birth")
    birth_time: Optional[time] = Field(None, description="Time of birth if known")
    time_zone: str = Field(..., min_length=1, description="IANA time zone identifier")
    location: BirthLocation = Field(..., description="Birth location coordinates and metadata")
    preferences: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional user preferences that influence report rendering"
    )


class PlanetPosition(BaseModel):
    """A planetary position for a chart."""

    planet: str = Field(..., description="Planet or luminary name")
    sign: str = Field(..., description="Zodiac sign the planet occupies")
    house: Optional[int] = Field(None, ge=1, le=12, description="Associated astrological house")
    degree: float = Field(..., ge=0.0, le=360.0, description="Absolute ecliptic degree")
    retrograde: bool = Field(False, description="Whether the planet is in retrograde motion")

    @validator("sign")
    def normalize_sign(cls, value: str) -> str:  # noqa: D401, N805 - required signature for Pydantic validator
        """Normalize sign names by capitalising the first letter."""

        return value.title()


class HousePosition(BaseModel):
    """House cusp information for a chart."""

    house: int = Field(..., ge=1, le=12, description="Astrological house number")
    sign: str = Field(..., description="Zodiac sign on the house cusp")
    degree: float = Field(..., ge=0.0, le=360.0, description="Degree position on the ecliptic")


class Aspect(BaseModel):
    """Aspect between two chart bodies."""

    aspect: str = Field(..., description="Name of the aspect e.g. Conjunction, Trine")
    orb: float = Field(..., ge=0.0, description="Orb difference in degrees")
    source: str = Field(..., description="Source planet or point")
    target: str = Field(..., description="Target planet or point")


class ChartMetadata(BaseModel):
    """Descriptive metadata for a generated chart."""

    chart_type: str = Field(..., description="Type of the chart e.g. natal, transit")
    computation_time: datetime = Field(..., description="Timestamp when computation completed")
    algorithm_version: str = Field(..., description="Version identifier for the computation engine")
    source_url: Optional[HttpUrl] = Field(
        None,
        description="Optional URL referencing the ephemeris or computation source",
    )


class ChartData(BaseModel):
    """Computed chart data returned to consumers."""

    id: UUID = Field(..., description="Unique identifier assigned to the generated chart")
    metadata: ChartMetadata
    planet_positions: List[PlanetPosition] = Field(default_factory=list)
    house_positions: List[HousePosition] = Field(default_factory=list)
    aspects: List[Aspect] = Field(default_factory=list)


class ChartComputationResponse(BaseModel):
    """Wrapper returned after chart generation."""

    chart: ChartData
    generated_report_id: Optional[UUID] = Field(
        None,
        description="Identifier for an associated narrative report if generated",
    )


class ReportSection(BaseModel):
    """A section of a generated astrology report."""

    title: str = Field(..., description="Section heading")
    summary: Optional[str] = Field(None, description="Short summary for the section")
    content: str = Field(..., description="Full narrative text for the section")


class ReportPayload(BaseModel):
    """Structured payload delivered to clients when requesting reports."""

    id: UUID = Field(..., description="Report identifier")
    chart_id: UUID = Field(..., description="Identifier of the chart the report references")
    generated_at: datetime = Field(..., description="Timestamp when the report was generated")
    sections: List[ReportSection] = Field(..., description="Narrative sections comprising the report")
    shareable_url: Optional[HttpUrl] = Field(
        None,
        description="Optional URL that can be shared to view the report",
    )


class AnalyticsBreakdown(BaseModel):
    """Breakdown metrics for analytics endpoints."""

    dimension: str = Field(..., description="Grouping dimension e.g. chart_type")
    results: Dict[str, int] = Field(..., description="Aggregated counts keyed by dimension value")


class AnalyticsSummary(BaseModel):
    """Top-level analytics response payload."""

    total_charts: int = Field(..., ge=0, description="Number of charts generated in the window")
    total_reports: int = Field(..., ge=0, description="Number of narrative reports delivered")
    breakdowns: List[AnalyticsBreakdown] = Field(
        default_factory=list,
        description="Breakdowns over selected dimensions",
    )


__all__ = [
    "AnalyticsBreakdown",
    "AnalyticsSummary",
    "Aspect",
    "BirthDataInput",
    "BirthLocation",
    "ChartComputationResponse",
    "ChartData",
    "ChartMetadata",
    "HousePosition",
    "PlanetPosition",
    "ReportPayload",
    "ReportSection",
]
