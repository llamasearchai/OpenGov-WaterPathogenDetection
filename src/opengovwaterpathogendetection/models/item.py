"""Data models for OpenGov-WaterPathogenDetection.

Core Item models used by the storage and API layers.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    """Base fields for an Item record."""

    name: str = Field(..., description="Human-readable item name")
    description: str = Field(..., description="Item description / notes")


class ItemCreate(ItemBase):
    """Item creation model (id & timestamps assigned server-side)."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp (UTC)")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp (UTC)")


class Item(ItemBase):
    """Full Item model persisted in the database."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}