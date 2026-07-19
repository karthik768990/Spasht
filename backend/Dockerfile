FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ /app/

# Copy sample documents to root so absolute paths in code still work
COPY sample_documents/ /sample_documents/

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
