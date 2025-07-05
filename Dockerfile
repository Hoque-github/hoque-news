# Use Python 3.10 as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all files to container
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Start the app using gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
