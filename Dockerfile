FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY backend ./backend
COPY .env.example ./.env.example

RUN pip install --upgrade pip && pip install -e .

EXPOSE 9090

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "9090"]