from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Branch(Base):
    __tablename__ = "branches"

    branch_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    branch_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    region: Mapped[str] = mapped_column(String(80), nullable=False)
    opened_at: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    incidents: Mapped[list["Incident"]] = relationship(back_populates="branch")


class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    business_domain: Mapped[str] = mapped_column(String(100), nullable=False)
    requires_followup: Mapped[bool] = mapped_column(Boolean, nullable=False)

    incidents: Mapped[list["Incident"]] = relationship(back_populates="category")


class Incident(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.branch_id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.category_id"), nullable=False, index=True)
    severity_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    affected_users: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_hours: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    branch: Mapped[Branch] = relationship(back_populates="incidents")
    category: Mapped[Category] = relationship(back_populates="incidents")
