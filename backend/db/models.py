"""SQLAlchemy ORM models for Kundali backend."""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for ORM models."""

    pass


class TimestampMixin:
    """Mixin providing timestamp columns."""

    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class UserProfile(TimestampMixin, Base):
    """Represents an application user profile."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    birth_time: Mapped[Optional[time]] = mapped_column(Time(timezone=False), nullable=True)
    time_zone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    location: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    charts: Mapped[list["SavedChart"]] = relationship(
        "SavedChart", back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[list["OrderHistory"]] = relationship(
        "OrderHistory", back_populates="user", cascade="all, delete-orphan"
    )


class SavedChart(TimestampMixin, Base):
    """Persisted chart computation for quick retrieval."""

    __tablename__ = "saved_charts"
    __table_args__ = (
        UniqueConstraint("user_id", "chart_type", "generated_at", name="uq_chart_user_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=True
    )
    chart_type: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    chart_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(1024))
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="charts")
    orders: Mapped[list["OrderHistory"]] = relationship(
        "OrderHistory", back_populates="chart", cascade="all, delete-orphan"
    )


class OrderHistory(TimestampMixin, Base):
    """Represents purchase history for premium reports or charts."""

    __tablename__ = "order_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    chart_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("saved_charts.id"), nullable=True
    )
    product_sku: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    fulfilled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivery_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="orders")
    chart: Mapped[Optional["SavedChart"]] = relationship("SavedChart", back_populates="orders")


__all__ = ["Base", "OrderHistory", "SavedChart", "UserProfile"]
