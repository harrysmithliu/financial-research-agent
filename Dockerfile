FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY pyproject.toml README.md LICENSE ./
COPY agents ./agents
COPY api ./api
COPY config ./config
COPY data ./data
COPY eval ./eval
COPY ingestion ./ingestion
COPY llm ./llm
COPY mcp_gateway ./mcp_gateway
COPY mcp_server ./mcp_server
COPY observability ./observability
COPY retrieval ./retrieval
COPY storage ./storage

RUN python -m pip install .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
