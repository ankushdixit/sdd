"""
Example SQLModel model demonstrating best practices
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    """Base model with shared fields."""

    name: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: float = Field(gt=0)
    is_active: bool = Field(default=True)


class Item(ItemBase, table=True):
    """
    Item database model.

    Attributes:
        id: Primary key
        name: Item name
        description: Item description
        price: Item price (must be > 0)
        is_active: Whether item is active
        created_at: Timestamp when item was created
        updated_at: Timestamp when item was last updated
    """

    __tablename__ = "items"  # pyright: ignore[reportAssignmentType]

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ItemCreate(ItemBase):
    """Schema for creating a new item."""

    pass


class ItemRead(ItemBase):
    """Schema for reading an item (includes id and timestamps)."""

    id: int
    created_at: datetime
    updated_at: datetime


class ItemUpdate(SQLModel):
    """Schema for updating an item (all fields optional)."""

    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: Optional[float] = Field(default=None, gt=0)
    is_active: Optional[bool] = None
