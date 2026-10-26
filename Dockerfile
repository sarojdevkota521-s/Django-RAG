# ==============================================================================
# Multi-stage production Dockerfile for Django RAG
# Optimized for FastEmbed, ONNX Runtime, and LangChain with Google Gemini
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build stage
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies into user local
COPY rag-prod/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Final minimal production runtime image
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Essential Python runtime environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8000

# Install runtime system libraries:
# - libgomp1: required by FastEmbed / ONNX Runtime (OpenMP support on Linux)
# - curl: required for container HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and application directories
RUN useradd -u 1000 -m -s /bin/bash appuser && \
    mkdir -p /app /app/uploads /app/staticfiles /app/data && \
    chown -R appuser:appuser /home/appuser /app

WORKDIR /app

# Copy pre-installed Python dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application source code
COPY --chown=appuser:appuser rag-prod/ /app/
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh

# Ensure Linux executable permissions and strip Windows CRLF line endings
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
