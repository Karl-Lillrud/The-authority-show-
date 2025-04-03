# Base image for Flask app
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY src/requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src /app/

# Expose the port Flask runs on
EXPOSE 8000

# Command to run the app
CMD ["python", "app.py"]
