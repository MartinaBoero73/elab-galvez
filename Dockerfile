# 1. Base OS: Python 3.12 (Slim version to reduce size)
FROM python:3.12-slim

# 2. System dependencies for Matplotlib and ReportLab (C compilers and image libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Install 'uv' directly from Astral's official image (ultra-fast installs)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4. Set the working directory
WORKDIR /app

# 5. Copy dependency files (supports both pyproject.toml or requirements.txt)
COPY pyproject.toml uv.lock* requirements.txt* ./

# 6. Install dependencies globally inside the container using uv
RUN if [ -f "pyproject.toml" ]; then uv pip install --system -r pyproject.toml; \
    elif [ -f "requirements.txt" ]; then uv pip install --system -r requirements.txt; \
    fi

# 7. Copy the application source code
COPY src/ ./src/

# 8. Set the Python path so it finds 'elab_galvez' correctly
ENV PYTHONPATH=/app/src

# 9. Railway dynamically assigns the PORT environment variable. We default to 8000.
ENV PORT=8000
EXPOSE ${PORT}

# 10. Entrypoint: Start Uvicorn pointing to our isolated main file
CMD ["sh", "-c", "uvicorn elab_galvez.main:app --host 0.0.0.0 --port ${PORT}"]