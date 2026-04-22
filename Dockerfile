FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

COPY tripmate/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY tripmate/ .

RUN python init_db.py

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
