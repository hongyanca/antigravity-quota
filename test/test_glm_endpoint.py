"""Tests for GLM endpoint formatting logic."""

import pytest

from src.api import format_percentage_with_color
from src.zai_client import format_glm_quota, process_quota_limit


class TestProcessQuotaLimit:
    """Tests for process_quota_limit function."""

    def test_process_quota_limit_with_valid_data(self):
        """Test quota limit processing with valid data."""
        raw_data = {
            "limits": [
                {"type": "TOKENS_LIMIT", "percentage": 1},
                {
                    "type": "TIME_LIMIT",
                    "percentage": 0,
                    "currentValue": 0,
                    "usage": 100,
                    "usageDetails": [
                        {"modelCode": "search-prime", "usage": 0},
                        {"modelCode": "web-reader", "usage": 0},
                        {"modelCode": "zread", "usage": 0},
                    ],
                },
            ]
        }

        result = process_quota_limit(raw_data)

        assert "limits" in result
        assert len(result["limits"]) == 2
        assert result["limits"][0]["type"] == "Token usage(5 Hour)"
        assert result["limits"][0]["percentage"] == 1
        assert result["limits"][1]["type"] == "MCP usage(1 Month)"
        assert result["limits"][1]["percentage"] == 0
        assert result["limits"][1]["currentUsage"] == 0
        assert result["limits"][1]["total"] == 100
        assert len(result["limits"][1]["usageDetails"]) == 3

    def test_process_quota_limit_with_empty_data(self):
        """Test quota limit processing with empty data."""
        result = process_quota_limit({})
        assert result == {}

    def test_process_quota_limit_with_no_limits(self):
        """Test quota limit processing with no limits."""
        result = process_quota_limit({"limits": []})
        assert result == {"limits": []}


class TestFormatGlmQuota:
    """Tests for format_glm_quota function."""

    def test_format_glm_quota_with_valid_data(self):
        """Test GLM quota formatting with valid data."""
        processed_data = {
            "limits": [
                {
                    "type": "MCP usage(1 Month)",
                    "percentage": 0,
                    "currentUsage": 0,
                    "total": 100,
                    "usageDetails": [
                        {"modelCode": "search-prime", "usage": 0},
                        {"modelCode": "web-reader", "usage": 0},
                        {"modelCode": "zread", "usage": 0},
                    ],
                },
                {"type": "Token usage(5 Hour)", "percentage": 1},
            ]
        }

        result = format_glm_quota(processed_data)

        assert "models" in result
        assert "last_updated" in result
        assert "is_forbidden" in result
        assert result["is_forbidden"] is False
        assert isinstance(result["last_updated"], int)

        # Check models
        models = result["models"]
        assert len(models) == 4  # glm, mcp-monthly, search-prime, web-reader (no zread)

        model_names = [m["name"] for m in models]
        assert "glm" in model_names
        assert "glm-coding-plan-mcp-monthly" in model_names
        assert "glm-coding-plan-search-prime" in model_names
        assert "glm-coding-plan-web-reader" in model_names

        # Check zread is excluded
        assert "glm-coding-plan-zread" not in model_names

        # Check that reset_time is not in any model
        for model in models:
            assert "reset_time" not in model
            assert "name" in model
            assert "percentage" in model

    def test_format_glm_quota_percentage_inversion(self):
        """Test that percentages are inverted (remaining = 100 - used)."""
        processed_data = {
            "limits": [
                {"type": "Token usage(5 Hour)", "percentage": 25},
                {
                    "type": "MCP usage(1 Month)",
                    "percentage": 10,
                    "currentUsage": 10,
                    "total": 100,
                    "usageDetails": [
                        {"modelCode": "search-prime", "usage": 5},
                        {"modelCode": "web-reader", "usage": 3},
                    ],
                },
            ]
        }

        result = format_glm_quota(processed_data)
        models = result["models"]

        glm_model = next(m for m in models if m["name"] == "glm")
        assert glm_model["percentage"] == 75  # 100 - 25

        mcp_model = next(m for m in models if m["name"] == "glm-coding-plan-mcp-monthly")
        assert mcp_model["percentage"] == 90  # 100 - 10

        search_model = next(m for m in models if m["name"] == "glm-coding-plan-search-prime")
        assert search_model["percentage"] == 95  # 100 - 5

        web_model = next(m for m in models if m["name"] == "glm-coding-plan-web-reader")
        assert web_model["percentage"] == 97  # 100 - 3

    def test_format_glm_quota_with_empty_data(self):
        """Test GLM quota formatting with empty data."""
        result = format_glm_quota({})

        assert result["models"] == []
        assert result["is_forbidden"] is False
        assert "last_updated" in result

    def test_format_glm_quota_with_no_limits(self):
        """Test GLM quota formatting with no limits."""
        result = format_glm_quota({"limits": []})

        assert result["models"] == []
        assert result["is_forbidden"] is False
        assert "last_updated" in result

    def test_format_glm_quota_excludes_zread(self):
        """Test that zread is excluded from MCP tool details."""
        processed_data = {
            "limits": [
                {
                    "type": "MCP usage(1 Month)",
                    "percentage": 0,
                    "currentUsage": 0,
                    "total": 100,
                    "usageDetails": [
                        {"modelCode": "zread", "usage": 10},
                    ],
                },
            ]
        }

        result = format_glm_quota(processed_data)
        models = result["models"]

        # Should only have the overall MCP quota, not zread
        assert len(models) == 1
        assert models[0]["name"] == "glm-coding-plan-mcp-monthly"

        model_names = [m["name"] for m in models]
        assert "glm-coding-plan-zread" not in model_names


class TestFormatPercentageWithColorForGLM:
    """Tests for format_percentage_with_color function used in GLM status."""

    def test_100_percent_returns_green_dot(self):
        """Test that 100% returns green dot."""
        result = format_percentage_with_color(100)
        assert "\033[32m" in result  # Green color
        assert "●" in result
        assert "\033[0m" in result  # Reset

    def test_0_percent_returns_red_dot(self):
        """Test that 0% returns red dot."""
        result = format_percentage_with_color(0)
        assert "\033[31m" in result  # Red color
        assert "●" in result
        assert "\033[0m" in result  # Reset

    def test_50_to_99_returns_green_percentage(self):
        """Test that 50-99% returns green percentage."""
        for pct in [50, 75, 99]:
            result = format_percentage_with_color(pct)
            assert "\033[32m" in result  # Green color
            assert f"{pct}%" in result
            assert "\033[0m" in result  # Reset

    def test_20_to_49_returns_yellow_percentage(self):
        """Test that 20-49% returns yellow percentage."""
        for pct in [20, 35, 49]:
            result = format_percentage_with_color(pct)
            assert "\033[33m" in result  # Yellow color
            assert f"{pct}%" in result
            assert "\033[0m" in result  # Reset

    def test_1_to_19_returns_red_percentage(self):
        """Test that 1-19% returns red percentage."""
        for pct in [1, 10, 19]:
            result = format_percentage_with_color(pct)
            assert "\033[31m" in result  # Red color
            assert f"{pct}%" in result
            assert "\033[0m" in result  # Reset
