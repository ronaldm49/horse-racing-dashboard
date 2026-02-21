FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user (optional for security, but render uses default user anyway)
# Let's keep it simple

COPY . .

# Expose port (Render sets PORT env variable)
EXPOSE 8000

# Start Uvicorn
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
