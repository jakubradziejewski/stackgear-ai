from urllib.parse import parse_qsl, urlsplit, urlunsplit, urlencode

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_CONNECT_TIMEOUT_SECONDS: float = 30.0
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GEMINI_API_KEY: str

    @property
    def _is_local(self) -> bool:
        """True when the DB host is localhost / 127.0.0.1 (dev machine)."""
        host = urlsplit(self.DATABASE_URL).hostname or ""
        return host in ("localhost", "127.0.0.1", "")

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL.strip()

        # Normalise the scheme so SQLAlchemy uses the asyncpg driver.
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            # Heroku / Railway still emit the legacy scheme.
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        # Strip ?sslmode=… — asyncpg handles SSL via connect_args, not the
        # query string.  Leaving it in causes an "unexpected keyword" error.
        parts = urlsplit(url)
        query_params = [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key.lower() != "sslmode"
        ]
        normalized_query = urlencode(query_params)

        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, normalized_query, parts.fragment)
        )

    @property
    def asyncpg_connect_args(self) -> dict[str, str | float]:
        args: dict[str, str | float] = {
            "timeout": self.DATABASE_CONNECT_TIMEOUT_SECONDS,
        }
        # Cloud providers (Neon, Supabase, Railway, Render) require SSL.
        # A local Postgres instance usually does not — forcing SSL there
        # raises "SSL is not enabled on the server".
        if not self._is_local:
            args["ssl"] = "require"
        return args

    class Config:
        env_file = ".env"


settings = Settings()