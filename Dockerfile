FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Initialize the mock database
RUN python -c "from centralign.runtime.verifier import TaskVerifier; TaskVerifier().reset_security_database()"

# Expose the port
EXPOSE 8000

# Run the FastAPI server
CMD ["python", "server.py", "--port", "8000", "--host", "0.0.0.0"]
