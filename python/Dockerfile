FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY pytest.ini .
COPY src/ ./src/
COPY tests/ ./tests/
COPY data/ ./data/
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
