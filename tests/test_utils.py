# tests/test_utils.py
import pytest
from app.utils.filters import format_datetime # Example: testing a filter
from datetime import datetime

def test_format_datetime_filter():
    dt = datetime(2024, 5, 1, 14, 30, 0)
    # Test medium format
    assert format_datetime(dt, format='medium') == 'May 01, 2024, 02:30 PM'
    # Test short_date format (should be MM/DD/YY)
    assert format_datetime(dt, format='short_date') == '05/01/24'
    assert format_datetime(None) == ""
    assert format_datetime("invalid string") == "invalid string"

# Add tests for other utils like validation, db helpers etc.