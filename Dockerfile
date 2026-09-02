FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8501

RUN groupadd --system praxa && useradd --system --gid praxa --create-home praxa
WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --requirement requirements.txt

COPY --chown=praxa:praxa . .
RUN mkdir -p /app/data/context /app/data/chromadb && chown -R praxa:praxa /app/data

USER praxa
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8501') + '/_stcore/health', timeout=3)"

CMD ["sh", "-c", "streamlit run praxa_client.py --server.address=0.0.0.0 --server.port=${PORT} --server.headless=true"]
