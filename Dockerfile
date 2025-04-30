# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt into the container at /app
COPY ./src/requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Make sure the app listens on all interfaces
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]

# Expose the port the app runs on
EXPOSE 8000
