# Dockerfile for the CreatorIQ FastAPI backend service.
FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies required by psycopg2 and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies before copying source code to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY . .

EXPOSE 8000

# Run Alembic database migrations, then start the Uvicorn ASGI server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
