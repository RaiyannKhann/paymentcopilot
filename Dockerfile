FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Bake model weights at build time so the container needs no network access at
# runtime (avoids cold-start latency and Hugging Face Hub rate limits).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
RUN python -m spacy download en_core_web_sm

COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps .

COPY scripts/ ./scripts/
COPY data/ ./data/

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "paymentcopilot.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
