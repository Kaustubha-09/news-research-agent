FROM python:3.11-slim

# uv itself is just a static binary — copying it from its official image
# is faster than pip-installing it inside our own image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy only dependency files first, so Docker can cache this layer —
# if only application code changes later, this expensive install step
# is skipped on rebuild instead of re-running every time.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Now copy the actual application code
COPY api.py phase6_image_generation.py ./

# Generated images are written here at runtime — Azure Container Apps has
# no volume mount like our local `docker run -v`, so the directory must
# already exist in the image or StaticFiles fails to even start.
RUN mkdir -p outputs

EXPOSE 8000

# uv run handles activating the project's venv for us
CMD ["uv", "run", "uvicorn", "api:api", "--host", "0.0.0.0", "--port", "8000"]
