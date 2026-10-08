FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY services /app/services
COPY database /app/database
RUN useradd --create-home clientpulse && mkdir -p /app/data && chown -R clientpulse:clientpulse /app
USER clientpulse
EXPOSE 8000
CMD ["uvicorn","services.api.main:app","--host","0.0.0.0","--port","8000"]
