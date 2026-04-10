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
    def async_database_url(self) -> str:
        url = self.DATABASE_URL.strip()

        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

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
        return {
            "ssl": "require",
            "timeout": self.DATABASE_CONNECT_TIMEOUT_SECONDS,
        }

    class Config:
        env_file = ".env"

settings = Settings()
