FROM python:3.12-slim

WORKDIR /app

# Set PYTHONPATH to include the src directory
ENV PYTHONPATH=/app/src

# Copy only requirements.txt first to leverage Docker caching
COPY src/requirements.txt src/requirements.txt

# Copy the .env file from the root directory to /app/src/
COPY .env /app/src/

# Install dependencies
RUN pip install -r src/requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port Flask will run on
EXPOSE 8000

# Run Gunicorn to serve the Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "src.app:app"]
