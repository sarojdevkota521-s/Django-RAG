# Django-RAG

Production-ready Retrieval-Augmented Generation (RAG) web application powered by **Django**, **LangChain**, **Google Gemini**, **FastEmbed**, and **Qdrant**.

---

## 🚀 Running with Docker

### Option 1: Using Docker Compose (Recommended)

1. Make sure your environment variables in `rag-prod/.env` are populated (`GOOGLE_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`).
2. Build and start the container:
   ```bash
   docker compose up --build
   ```
3. Open your browser at:
   ```
   http://localhost:8000
   ```

### Option 2: Using Plain Docker

1. **Build the image**:
   ```bash
   docker build -t django-rag .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 --env-file rag-prod/.env django-rag
   ```

---

## 🛠️ Docker Architecture Highlights

- **Multi-Stage Build**: Keeps the final production image slim by isolating build-time compilers and caching wheel installations.
- **FastEmbed & ONNX Runtime Support**: Includes `libgomp1` (OpenMP) required for high-performance ONNX vector embeddings under Linux.
- **Security**: Runs under a dedicated unprivileged user (`appuser`).
- **Automatic Migration & Asset Collection**: Database migrations and static collection are executed seamlessly on container startup via `entrypoint.sh`.
- **Production WSGI Server**: Powered by `gunicorn` with configurable workers and timeouts.
- **Static Assets with WhiteNoise**: Automatically serves static files in production without requiring a standalone Nginx proxy.

---

