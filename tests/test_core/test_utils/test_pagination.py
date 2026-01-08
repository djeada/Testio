"""Tests for the pagination utility module."""
import sys

sys.path.append(".")

import pytest

from src.core.utils.pagination import (
    PaginationParams,
    PaginatedResponse,
    paginate,
    encode_cursor,
    decode_cursor
)


class TestPaginationParams:
    """Test suite for PaginationParams."""

    def test_default_values(self):
        """Test default pagination values."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_offset_calculation(self):
        """Test offset calculation for different pages."""
        params = PaginationParams(page=1, page_size=10)
        assert params.offset == 0

        params = PaginationParams(page=2, page_size=10)
        assert params.offset == 10

        params = PaginationParams(page=5, page_size=20)
        assert params.offset == 80

    def test_limit_property(self):
        """Test that limit equals page_size."""
        params = PaginationParams(page=3, page_size=25)
        assert params.limit == 25


class TestPaginatedResponse:
    """Test suite for PaginatedResponse."""

    def test_create_from_items(self):
        """Test creating a paginated response."""
        response = PaginatedResponse.create(
            items=["a", "b", "c"],
            total_items=10,
            page=1,
            page_size=3
        )
        
        assert response.items == ["a", "b", "c"]
        assert response.total_items == 10
        assert response.total_pages == 4
        assert response.current_page == 1
        assert response.page_size == 3
        assert response.has_next is True
        assert response.has_previous is False

    def test_last_page(self):
        """Test last page has no next page."""
        response = PaginatedResponse.create(
            items=["a"],
            total_items=7,
            page=4,
            page_size=2
        )
        
        assert response.has_next is False
        assert response.has_previous is True

    def test_single_page(self):
        """Test single page has no next or previous."""
        response = PaginatedResponse.create(
            items=["a", "b"],
            total_items=2,
            page=1,
            page_size=10
        )
        
        assert response.total_pages == 1
        assert response.has_next is False
        assert response.has_previous is False

    def test_empty_items(self):
        """Test response with no items."""
        response = PaginatedResponse.create(
            items=[],
            total_items=0,
            page=1,
            page_size=10
        )
        
        assert response.items == []
        assert response.total_items == 0
        assert response.total_pages == 1


class TestPaginateFunction:
    """Test suite for paginate function."""

    def test_paginate_first_page(self):
        """Test paginating first page."""
        items = list(range(100))
        result = paginate(items, page=1, page_size=10)
        
        assert result.items == list(range(10))
        assert result.total_items == 100
        assert result.total_pages == 10
        assert result.current_page == 1

    def test_paginate_middle_page(self):
        """Test paginating middle page."""
        items = list(range(100))
        result = paginate(items, page=5, page_size=10)
        
        assert result.items == list(range(40, 50))
        assert result.current_page == 5

    def test_paginate_last_page(self):
        """Test paginating last page."""
        items = list(range(25))
        result = paginate(items, page=3, page_size=10)
        
        assert result.items == list(range(20, 25))
        assert result.has_next is False

    def test_paginate_beyond_range(self):
        """Test paginating beyond available items."""
        items = list(range(10))
        result = paginate(items, page=5, page_size=10)
        
        assert result.items == []
        assert result.total_items == 10


class TestCursorEncoding:
    """Test suite for cursor encoding/decoding."""

    def test_encode_decode_string(self):
        """Test encoding and decoding a string."""
        original = "some-value-123"
        encoded = encode_cursor(original)
        decoded = decode_cursor(encoded)
        assert decoded == original

    def test_encode_decode_integer(self):
        """Test encoding and decoding an integer."""
        original = 12345
        encoded = encode_cursor(original)
        decoded = decode_cursor(encoded)
        assert decoded == str(original)

    def test_encoded_is_urlsafe(self):
        """Test that encoded cursor is URL-safe."""
        original = "value/with+special=chars"
        encoded = encode_cursor(original)
        # URL-safe base64 uses - and _ instead of + and /
        assert "+" not in encoded
        assert "/" not in encoded
