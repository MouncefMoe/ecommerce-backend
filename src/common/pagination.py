"""Pagination utilities."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = 1
    size: int = 20

    @property
    def skip(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )
