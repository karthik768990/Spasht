FROM python:3.11-slim

WORKDIR /app

# Install CPU-only torch explicitly BEFORE the rest of requirements.txt,
# so pip doesn't pull the default CUDA build as a transitive dependency
# of sentence-transformers.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/
COPY sample_documents/ /sample_documents/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
