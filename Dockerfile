FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD alembic upgrade head; uvicorn app.main:app --host 0.0.0.0
