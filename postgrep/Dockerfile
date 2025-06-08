# Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    supervisor\
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy the rest of the application code into the container at /app
COPY . .


# Copy the supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf


# Expose the port the API will run on
EXPOSE 8000
EXPOSE 8001

# Run supervisor when the container starts
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
