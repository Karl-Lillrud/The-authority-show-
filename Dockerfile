# Use a specific Python version for the base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements.txt first to leverage Docker caching
COPY src/requirements.txt /app/src/

# Install dependencies
RUN pip install --no-cache-dir -r /app/src/requirements.txt  

# Copy the entire application code from the src folder into /app/src/
COPY src /app/src/

# Expose the port that the app will run on
EXPOSE 8000

# Set the environment variable for Python to ensure non-buffered output (important for logs)
ENV PYTHONUNBUFFERED=1

# Use gunicorn to run the application with appropriate settings
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "src.app:app"]
