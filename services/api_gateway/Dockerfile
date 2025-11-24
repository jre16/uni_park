FROM python:3.13-slim

WORKDIR /app

COPY services/api_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/api_gateway/main.py .

# Copy static files and templates from parent directory (using build context)
COPY static /app/static
COPY services/api_gateway/templates /app/templates
RUN mkdir -p /app/media/qr_codes

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
