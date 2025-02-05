FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy into container
COPY . .

# Expose port
EXPOSE 8050

# Define command
CMD ["python", "app.py"]
