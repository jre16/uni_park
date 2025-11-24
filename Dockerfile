FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better caching)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary dirs
RUN mkdir -p /app/media/qr_codes

# Collect static files during build
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Run Django server
CMD ["gunicorn", "unipark.wsgi:application", "--bind", "0.0.0.0:8000"]
