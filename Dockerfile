# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for psycopg2 and other tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Download AlloyDB Auth Proxy binary for deployment execution (Option C)
RUN wget https://storage.googleapis.com/alloydb-auth-proxy/v1.14.2/alloydb-auth-proxy.linux.amd64 -O alloydb-auth-proxy \
    && chmod +x alloydb-auth-proxy \
    && chmod +x start.sh

# Expose the port (Cloud Run sets PORT env var automatically)
EXPOSE 8080

# Run the app via the proxy shell script
CMD ["./start.sh"]
