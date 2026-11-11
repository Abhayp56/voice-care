import pytest
from unittest.mock import patch, MagicMock
from app.database.supabase_client import (
    get_supabase_client,
    get_supabase_anon_client,
    check_supabase_connection,
    SupabaseConfigurationError,
    SupabaseConnectionError
)


def test_supabase_config_error_when_missing_keys():
    with patch("app.database.supabase_client.settings") as mock_settings:
        mock_settings.SUPABASE_URL = ""
        mock_settings.SUPABASE_SERVICE_ROLE_KEY = ""
        with patch("app.database.supabase_client._supabase_admin_client", None):
            with pytest.raises(SupabaseConfigurationError):
                get_supabase_client()


def test_supabase_health_check_success():
    with patch("app.database.supabase_client.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.count = 4
        mock_response.data = [{"id": "1"}, {"id": "2"}]
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response
        mock_get_client.return_value = mock_client

        health = check_supabase_connection()
        assert health["status"] == "connected"
        assert health["database"] == "reachable"


def test_supabase_health_check_failure():
    with patch("app.database.supabase_client.get_supabase_client") as mock_get_client:
        mock_get_client.side_effect = Exception("Connection timed out")

        health = check_supabase_connection()
        assert health["status"] == "error"
        assert health["database"] == "unreachable"
        assert "timed out" in health["error"]

