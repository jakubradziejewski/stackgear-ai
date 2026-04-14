FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock* ./

# Install production deps only
RUN uv sync --no-dev

# Copy source
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]