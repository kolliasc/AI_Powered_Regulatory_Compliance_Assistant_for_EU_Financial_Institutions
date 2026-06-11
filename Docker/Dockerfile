# EU Compliance Assistant — RAG API (PoC)
#
# Build from the PROJECT ROOT so the context includes src/ and data/:
#   docker build -f Docker/Dockerfile -t eu-compliance-assistant .
#
# Run (needs the Azure OpenAI + JWT vars — pass your local .env):
#   docker run --rm -p 8000:8000 --env-file .env eu-compliance-assistant
#
# Then open frontend/index.html in a browser (it calls http://localhost:8000),
# or use the Swagger UI at http://localhost:8000/docs.

FROM python:3.11-slim

# Use the base interpreter; let uv manage deps from the committed uv.lock.
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH=/app/.venv/bin:$PATH

RUN pip install --no-cache-dir uv

WORKDIR /app

# 1. Dependencies only (cached layer). --no-install-project: we run via `src.` on
#    PYTHONPATH, so the project itself doesn't need a build backend.
#    NOTE: if a wheel ever needs compiling on your build host, add build-essential.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2. Bake the embedding model so the container needs no internet at runtime.
#    Must match settings.EMBEDDING_MODEL_NAME.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# 3. App code + prebuilt Chroma vector DB + source PDFs.
#    (databricks_code*, *_staging.json and *.zip are excluded via .dockerignore.)
COPY src ./src
COPY data ./data

EXPOSE 8000

# app_state.py builds the embedder/vector-store/LLM at import; bind 0.0.0.0 for the port map.
CMD ["uvicorn", "src.API_RAG:app", "--host", "0.0.0.0", "--port", "8000"]