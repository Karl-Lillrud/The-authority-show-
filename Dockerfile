FROM python:3.10-slim

WORKDIR /app

# Set PYTHONPATH to include the src directory
ENV PYTHONPATH=/app/src

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker caching
COPY src/requirements.txt /app/src/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/src/requirements.txt
RUN pip install --no-cache-dir gunicorn

# Ensure .env file is in the build context (project root) and not listed in .dockerignore
# Copy the .env file from the root directory of the build context to /app/.env in the image
COPY ./.env /app/.env

# Copy the rest of the application
COPY src/ /app/src/

# Expose the port Flask will run on
EXPOSE 8000

ENV GUNICORN_SEND_FILE=0

# Run Gunicorn to serve the Flask app
CMD ["gunicorn","--bind", "0.0.0.0:8000","--worker-class=sync","--workers=4","--threads=2","--timeout=120","--keep-alive=5","--graceful-timeout=30","--worker-tmp-dir=/dev/shm","src.app:app"]