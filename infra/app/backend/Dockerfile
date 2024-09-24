# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy only the poetry files to cache them in Docker layer
COPY ./pyproject.toml ./poetry.lock ./

# Copy the entire directory to check the structure
COPY ./infra/app/backend ./

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Install uvicorn to run the app
RUN pip install uvicorn

# Expose the port the app runs on
EXPOSE 80

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
