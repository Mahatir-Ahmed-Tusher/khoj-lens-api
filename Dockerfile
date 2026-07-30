FROM python:3.11-slim

# Set working dir
WORKDIR /app

# Install system dependencies required for lxml and other libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev libxslt1-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml pyproject.toml
COPY PicImageSearch/ PicImageSearch/
COPY api/ api/

# Install runtime dependencies
# We install fastapi and uvicorn, then install the package itself
RUN pip install --no-cache-dir "uvicorn[standard]" "fastapi" && \
    pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
