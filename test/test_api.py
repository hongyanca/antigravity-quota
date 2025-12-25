"""Tests for src.api module."""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api import (
    app,
    filter_models,
    format_quota,
    format_time_remaining,
)


class TestFormatTimeRemaining:
    """Tests for format_time_remaining function."""

    def test_future_time(self):
        """Test formatting a future reset time."""
        future = datetime.now(timezone.utc) + timedelta(hours=4, minutes=30)
        result = format_time_remaining(future.isoformat())
        # Allow for test execution time (could be 4h 29m or 4h 30m)
        assert result in ("4h 29m", "4h 30m")

    def test_past_time_returns_reset_due(self):
        """Test that past time returns 'Reset due'."""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        result = format_time_remaining(past.isoformat())
        assert result == "Reset due"

    def test_z_suffix_timezone(self):
        """Test parsing time with Z suffix."""
        future = datetime.now(timezone.utc) + timedelta(hours=2, minutes=15)
        time_str = future.strftime("%Y-%m-%dT%H:%M:%SZ")
        result = format_time_remaining(time_str)
        # Allow for test execution time (could be 2h 14m or 2h 15m)
        assert result in ("2h 14m", "2h 15m")

    def test_invalid_time_returns_empty(self):
        """Test that invalid time string returns empty string."""
        result = format_time_remaining("invalid-time")
        assert result == ""


class TestFormatQuota:
    """Tests for format_quota function."""

    def test_format_gemini_models(self):
        """Test formatting Gemini models."""
        quota_data = {
            "models": {
                "gemini-3-pro-high": {
                    "quotaInfo": {
                        "remainingFraction": 0.85,
                        "resetTime": "2025-12-26T00:00:00Z",
                    }
                },
                "gemini-3-flash": {
                    "quotaInfo": {
                        "remainingFraction": 1.0,
                        "resetTime": "2025-12-26T00:00:00Z",
                    }
                },
            }
        }
        result = format_quota(quota_data, show_relative=False)

        assert len(result["models"]) == 2
        assert result["models"][0]["name"] == "gemini-3-flash"
        assert result["models"][0]["percentage"] == 100
        assert result["models"][1]["name"] == "gemini-3-pro-high"
        assert result["models"][1]["percentage"] == 85
        assert result["is_forbidden"] is False

    def test_format_claude_models(self):
        """Test formatting Claude models."""
        quota_data = {
            "models": {
                "claude-sonnet-4-5": {
                    "quotaInfo": {
                        "remainingFraction": 0.50,
                        "resetTime": "2025-12-26T00:00:00Z",
                    }
                },
            }
        }
        result = format_quota(quota_data, show_relative=False)

        assert len(result["models"]) == 1
        assert result["models"][0]["name"] == "claude-sonnet-4-5"
        assert result["models"][0]["percentage"] == 50

    def test_filters_non_gemini_claude_models(self):
        """Test that non-Gemini/Claude models are filtered out."""
        quota_data = {
            "models": {
                "some-other-model": {
                    "quotaInfo": {
                        "remainingFraction": 0.75,
                        "resetTime": "2025-12-26T00:00:00Z",
                    }
                },
            }
        }
        result = format_quota(quota_data, show_relative=False)
        assert len(result["models"]) == 0

    def test_empty_models(self):
        """Test handling empty models dict."""
        quota_data = {"models": {}}
        result = format_quota(quota_data)
        assert result["models"] == []
        assert "last_updated" in result


class TestFilterModels:
    """Tests for filter_models function."""

    def test_filter_by_pattern(self):
        """Test filtering models by pattern."""
        quota = {
            "models": [
                {"name": "gemini-3-pro-high", "percentage": 100},
                {"name": "gemini-3-pro-low", "percentage": 90},
                {"name": "gemini-3-flash", "percentage": 80},
                {"name": "claude-sonnet-4-5", "percentage": 70},
            ],
            "last_updated": 123456,
            "is_forbidden": False,
        }
        result = filter_models(quota, ["gemini-3-pro"])
        assert len(result["models"]) == 2
        assert all("gemini-3-pro" in m["name"] for m in result["models"])
        assert result["last_updated"] == 123456

    def test_filter_multiple_patterns(self):
        """Test filtering with multiple patterns."""
        quota = {
            "models": [
                {"name": "gemini-3-pro-high", "percentage": 100},
                {"name": "claude-sonnet-4-5", "percentage": 70},
            ],
            "last_updated": 123456,
            "is_forbidden": False,
        }
        result = filter_models(quota, ["gemini", "claude"])
        assert len(result["models"]) == 2

    def test_filter_no_matches(self):
        """Test filtering with no matches."""
        quota = {
            "models": [{"name": "gemini-3-pro-high", "percentage": 100}],
            "last_updated": 123456,
            "is_forbidden": False,
        }
        result = filter_models(quota, ["nonexistent"])
        assert len(result["models"]) == 0


class TestAPIEndpoints:
    """Integration tests for API endpoints using mocked data."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_quota_data(self):
        """Sample quota data for mocking."""
        return {
            "models": {
                "gemini-3-pro-high": {
                    "quotaInfo": {
                        "remainingFraction": 1.0,
                        "resetTime": "2025-12-26T00:00:00Z",
                    }
                },
                "gemini-3-flash": {
                    "quotaInfo": {
                        "remainingFraction": 0.9,
                        "resetTime": "2025-12-26T00:00:00Z",
                    }
                },
                "claude-sonnet-4-5": {
                    "quotaInfo": {
                        "remainingFraction": 0.8,
                        "resetTime": "2025-12-26T00:00:00Z",
                    }
                },
            }
        }

    @patch("src.api._get_quota_data")
    def test_get_all_quota(self, mock_get_quota, client, mock_quota_data):
        """Test /quota endpoint returns all models."""
        mock_get_quota.return_value = mock_quota_data

        response = client.get("/quota")

        assert response.status_code == 200
        data = response.json()
        assert "quota" in data
        assert len(data["quota"]["models"]) == 3

    @patch("src.api._get_quota_data")
    def test_get_gemini_3_pro(self, mock_get_quota, client, mock_quota_data):
        """Test /quota/gemini-3-pro endpoint."""
        mock_get_quota.return_value = mock_quota_data

        response = client.get("/quota/gemini-3-pro")

        assert response.status_code == 200
        data = response.json()
        assert len(data["quota"]["models"]) == 1
        assert "gemini-3-pro" in data["quota"]["models"][0]["name"]

    @patch("src.api._get_quota_data")
    def test_get_gemini_3_flash(self, mock_get_quota, client, mock_quota_data):
        """Test /quota/gemini-3-flash endpoint."""
        mock_get_quota.return_value = mock_quota_data

        response = client.get("/quota/gemini-3-flash")

        assert response.status_code == 200
        data = response.json()
        assert len(data["quota"]["models"]) == 1
        assert data["quota"]["models"][0]["name"] == "gemini-3-flash"

    @patch("src.api._get_quota_data")
    def test_get_claude_4_5(self, mock_get_quota, client, mock_quota_data):
        """Test /quota/claude-4-5 endpoint."""
        mock_get_quota.return_value = mock_quota_data

        response = client.get("/quota/claude-4-5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["quota"]["models"]) == 1
        assert "claude" in data["quota"]["models"][0]["name"]
