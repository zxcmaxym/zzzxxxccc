FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app .

# Create data directories
RUN mkdir -p /data/tasks /data/results /data/teachers /data/students

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/school_db

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 