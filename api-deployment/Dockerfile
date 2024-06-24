# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Install the dependencies
RUN pip install --no-cache-dir fastapi uvicorn kubernetes

# Copy the current directory contents into the container at /app
COPY main.py main.py

# Run uvicorn with our FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"] 
