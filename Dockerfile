# Dockerfile
FROM python:slim-bullseye

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY urlmanager.py .
COPY templates templates

EXPOSE 5000

CMD ["gunicorn","-b", "0.0.0.0:5000", "-w", "1", "--access-logfile", "-", "urlmanager:app"]
