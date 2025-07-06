FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install system dependencies including git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose any port — doesn't matter, Render overrides it
EXPOSE 5000

# IMPORTANT: Use "$PORT" only at runtime
#CMD ["gunicorn", "-b", "0.0.0.0:$PORT", "app:app"]
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:$PORT app:app"]