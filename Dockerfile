FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for psycopg2 and building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy all application code and static resources
COPY backend /app/backend
COPY data /app/data
COPY app.html /app/app.html
COPY food_bg.png /app/food_bg.png
COPY knime_etl_pipeline_1.png /app/knime_etl_pipeline_1.png
COPY knime_etl_pipeline_2.png /app/knime_etl_pipeline_2.png

# Expose port 8000
EXPOSE 8000

# Run database seed first, then start FastAPI server
CMD python -m backend.app.seed && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
