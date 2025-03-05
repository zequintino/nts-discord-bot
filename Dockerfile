# Start with the official Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# - libopus-dev: Required for Discord voice functionality
# - ffmpeg: Required for audio processing
# - build-essential and other dev packages: Required for building Python extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libopus-dev \
    ffmpeg \
    build-essential \
    python3-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "main.py"]

