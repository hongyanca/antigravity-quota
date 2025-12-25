"""Tests for src.cloudcode_client module."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.cloudcode_client import (
    ensure_fresh_token,
    load_account,
    normalize_account,
)


class TestLoadAccount:
    """Tests for load_account function."""

    def test_load_account_file_not_found(self):
        """Test that FileNotFoundError is raised when account file doesn't exist."""
        with patch("src.cloudcode_client.ACCOUNT_FILE", Path("/nonexistent/file.json")):
            with pytest.raises(FileNotFoundError, match="Account file not found"):
                load_account()

    def test_load_account_success(self, tmp_path):
        """Test successful account loading."""
        account_data = {"access_token": "test_token", "refresh_token": "test_refresh"}
        account_file = tmp_path / "account.json"
        account_file.write_text(json.dumps(account_data))

        with patch("src.cloudcode_client.ACCOUNT_FILE", account_file):
            result = load_account()
            assert result == account_data


class TestNormalizeAccount:
    """Tests for normalize_account function."""

    def test_normalize_token_format(self):
        """Test account with 'token' key format."""
        account = {
            "token": {
                "access_token": "access123",
                "refresh_token": "refresh456",
                "expiry_timestamp": 1234567890,
                "project_id": "project-123",
            }
        }
        access, refresh, expiry, project = normalize_account(account)
        assert access == "access123"
        assert refresh == "refresh456"
        assert expiry == 1234567890
        assert project == "project-123"

    def test_normalize_flat_format_with_timestamp(self):
        """Test flat account format with timestamp."""
        now_ms = int(time.time() * 1000)
        account = {
            "access_token": "access123",
            "refresh_token": "refresh456",
            "timestamp": now_ms,
            "expires_in": 3600,
            "project_id": "project-123",
        }
        access, refresh, expiry, project = normalize_account(account)
        assert access == "access123"
        assert refresh == "refresh456"
        assert expiry == (now_ms // 1000) + 3600
        assert project == "project-123"

    def test_normalize_flat_format_with_expiry_timestamp(self):
        """Test flat account format with expiry_timestamp."""
        account = {
            "access_token": "access123",
            "refresh_token": "refresh456",
            "expiry_timestamp": 1234567890,
        }
        access, refresh, expiry, project = normalize_account(account)
        assert access == "access123"
        assert refresh == "refresh456"
        assert expiry == 1234567890
        assert project is None

    def test_normalize_missing_fields(self):
        """Test account with missing fields returns None values."""
        account = {}
        access, refresh, expiry, project = normalize_account(account)
        assert access is None
        assert refresh is None
        assert expiry is None
        assert project is None


class TestEnsureFreshToken:
    """Tests for ensure_fresh_token function."""

    def test_missing_access_token_raises_error(self):
        """Test that ValueError is raised when access_token is missing."""
        account = {"refresh_token": "refresh123"}
        with pytest.raises(ValueError, match="Missing access_token or refresh_token"):
            ensure_fresh_token(account)

    def test_missing_refresh_token_raises_error(self):
        """Test that ValueError is raised when refresh_token is missing."""
        account = {"access_token": "access123"}
        with pytest.raises(ValueError, match="Missing access_token or refresh_token"):
            ensure_fresh_token(account)

    def test_fresh_token_returns_existing(self):
        """Test that fresh token is returned without refresh."""
        future_expiry = int(time.time()) + 600  # 10 minutes from now
        account = {
            "access_token": "access123",
            "refresh_token": "refresh456",
            "expiry_timestamp": future_expiry,
        }
        result = ensure_fresh_token(account)
        assert result == "access123"

    @patch("src.cloudcode_client.refresh_access_token")
    @patch("src.cloudcode_client.ACCOUNT_FILE", Path("/tmp/test_account.json"))
    def test_expired_token_refreshes(self, mock_refresh):
        """Test that expired token triggers refresh."""
        past_expiry = int(time.time()) - 100  # expired
        account = {
            "access_token": "old_access",
            "refresh_token": "refresh456",
            "expiry_timestamp": past_expiry,
        }
        mock_refresh.return_value = {
            "access_token": "new_access",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        with patch("builtins.open", mock_open()):
            result = ensure_fresh_token(account)

        assert result == "new_access"
        mock_refresh.assert_called_once_with("refresh456")
