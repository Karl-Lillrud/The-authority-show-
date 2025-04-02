# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker cache
COPY src/requirements.txt /app/src/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r src/requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose the ports for Flask and Streamlit
EXPOSE 8000 8501

# Command to run both Flask and Streamlit
CMD ["bash", "src/startup.sh"]
