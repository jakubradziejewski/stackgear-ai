"""
tests/test_db_config.py

Tests for config.py URL normalisation and SSL logic.
Run with:  pytest tests/test_db_config.py -v

No live database required — all tests mock the DATABASE_URL env var.
"""

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_settings(database_url: str):
    """Return a fresh Settings instance with the given DATABASE_URL."""
    # We patch os.environ so pydantic-settings picks up the value without
    # needing a real .env file on disk.
    env = {
        "DATABASE_URL": database_url,
        "SECRET_KEY": "test-secret",
        "GEMINI_API_KEY": "test-gemini-key",
    }
    with patch.dict("os.environ", env, clear=False):
        # Import inside the patch so the module re-reads env vars.
        from importlib import reload
        import app.core.config as cfg_module
        reload(cfg_module)
        from app.core.config import Settings
        return Settings()


# ---------------------------------------------------------------------------
# async_database_url — scheme normalisation
# ---------------------------------------------------------------------------

class TestAsyncDatabaseUrl:
    def test_postgresql_scheme_replaced(self):
        s = make_settings("postgresql://user:pass@db.example.com:5432/mydb")
        assert s.async_database_url.startswith("postgresql+asyncpg://")

    def test_legacy_postgres_scheme_replaced(self):
        """Railway / Heroku emit postgres://, not postgresql://."""
        s = make_settings("postgres://user:pass@db.example.com:5432/mydb")
        assert s.async_database_url.startswith("postgresql+asyncpg://")

    def test_sslmode_stripped_from_query_string(self):
        """asyncpg rejects sslmode in the URL — it must be removed."""
        s = make_settings(
            "postgresql://user:pass@db.example.com/mydb?sslmode=require"
        )
        assert "sslmode" not in s.async_database_url

    def test_other_query_params_preserved(self):
        """Only sslmode is stripped; other params must survive."""
        s = make_settings(
            "postgresql://user:pass@db.example.com/mydb"
            "?sslmode=require&application_name=hardware_hub"
        )
        assert "application_name=hardware_hub" in s.async_database_url
        assert "sslmode" not in s.async_database_url

    def test_already_asyncpg_scheme_untouched(self):
        """If someone already puts +asyncpg in the URL, don't double-replace."""
        s = make_settings("postgresql+asyncpg://user:pass@db.example.com/mydb")
        assert s.async_database_url.count("+asyncpg") == 1


# ---------------------------------------------------------------------------
# asyncpg_connect_args — SSL behaviour
# ---------------------------------------------------------------------------

class TestConnectArgs:
    def test_remote_host_requires_ssl(self):
        """Cloud providers need ssl='require'."""
        s = make_settings("postgresql://user:pass@db.neon.tech:5432/mydb")
        assert s.asyncpg_connect_args.get("ssl") == "require"

    def test_localhost_no_ssl(self):
        """Local Postgres must NOT get ssl='require' — it breaks."""
        s = make_settings("postgresql://user:pass@localhost:5432/mydb")
        assert "ssl" not in s.asyncpg_connect_args

    def test_127_no_ssl(self):
        s = make_settings("postgresql://user:pass@127.0.0.1:5432/mydb")
        assert "ssl" not in s.asyncpg_connect_args

    def test_timeout_always_present(self):
        """Timeout should be in connect_args regardless of host."""
        for url in [
            "postgresql://u:p@localhost/db",
            "postgresql://u:p@db.neon.tech/db",
        ]:
            s = make_settings(url)
            assert "timeout" in s.asyncpg_connect_args


# ---------------------------------------------------------------------------
# _is_local helper
# ---------------------------------------------------------------------------

class TestIsLocal:
    @pytest.mark.parametrize("url", [
        "postgresql://u:p@localhost/db",
        "postgresql://u:p@127.0.0.1/db",
    ])
    def test_local_urls(self, url):
        s = make_settings(url)
        assert s._is_local is True

    @pytest.mark.parametrize("url", [
        "postgresql://u:p@db.neon.tech/db",
        "postgresql://u:p@aws-0-eu-central.pooler.supabase.com/db",
        "postgresql://u:p@containers-us-west.railway.app/db",
    ])
    def test_remote_urls(self, url):
        s = make_settings(url)
        assert s._is_local is False