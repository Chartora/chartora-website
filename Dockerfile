# Multi-stage Dockerfile for Chartora.in Master Production Engine
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy application source code
COPY . /app

# Ensure correct permissions
RUN chmod +x /app/server.py

# Expose production port
EXPOSE 8080

# Environment variables
ENV APP_ENV=production
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Start Master SaaS Platform Server Engine
CMD ["python3", "server.py"]
