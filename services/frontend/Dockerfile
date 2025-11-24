FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Run migrations and start server
CMD python manage.py migrate --noinput && \
    python manage.py loaddata parking/fixtures/sample_data.json || true && \
    gunicorn unipark.wsgi:application --bind 0.0.0.0:8000 --workers 3
