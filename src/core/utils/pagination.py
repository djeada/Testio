"""
Pagination utilities for API endpoints.
Provides standardized pagination support for list endpoints.
"""

from dataclasses import dataclass
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, 
        ge=1, 
        le=100, 
        description="Number of items per page"
    )
    
    @property
    def offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get the limit for database queries."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""
    items: List[Any] = Field(description="List of items on the current page")
    total_items: int = Field(description="Total number of items across all pages")
    total_pages: int = Field(description="Total number of pages")
    current_page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")
    
    @classmethod
    def create(
        cls,
        items: List[Any],
        total_items: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse":
        """
        Create a paginated response from a list of items.
        
        :param items: Items on the current page
        :param total_items: Total number of items
        :param page: Current page number
        :param page_size: Items per page
        :return: PaginatedResponse instance
        """
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
        return cls(
            items=items,
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            has_next=page < total_pages,
            has_previous=page > 1
        )


def paginate(
    items: List[Any],
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse:
    """
    Paginate a list of items.
    
    :param items: Full list of items to paginate
    :param page: Page number (1-indexed)
    :param page_size: Items per page
    :return: PaginatedResponse with the requested page
    """
    total_items = len(items)
    offset = (page - 1) * page_size
    paginated_items = items[offset:offset + page_size]
    
    return PaginatedResponse.create(
        items=paginated_items,
        total_items=total_items,
        page=page,
        page_size=page_size
    )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters for large datasets."""
    cursor: Optional[str] = Field(
        default=None, 
        description="Cursor for the next page"
    )
    limit: int = Field(
        default=20, 
        ge=1, 
        le=100, 
        description="Number of items to return"
    )


class CursorPaginatedResponse(BaseModel):
    """Cursor-based paginated response."""
    items: List[Any] = Field(description="List of items")
    next_cursor: Optional[str] = Field(
        description="Cursor for the next page, None if no more items"
    )
    has_more: bool = Field(description="Whether there are more items")


def encode_cursor(value: Any) -> str:
    """
    Encode a value as a cursor string.
    
    :param value: Value to encode (typically an ID or timestamp)
    :return: Encoded cursor string
    """
    import base64
    return base64.urlsafe_b64encode(str(value).encode()).decode()


def decode_cursor(cursor: str) -> str:
    """
    Decode a cursor string.
    
    :param cursor: Encoded cursor string
    :return: Decoded value
    """
    import base64
    return base64.urlsafe_b64decode(cursor.encode()).decode()
