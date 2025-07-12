FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    libjpeg-dev zlib1g-dev libfreetype6-dev libpng-dev \
    libopenjp2-7 libssl-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "greetings:app", "--host", "0.0.0.0", "--port", "8000"]
