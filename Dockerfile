FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Dependências de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg imagemagick libsndfile1 git wget curl libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

# Instalar Requirements Serverless
COPY requirements.serverless.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir --force-reinstall -r /app/requirements.txt

# Copiar código
COPY . /app/

# Pastas necessárias
RUN mkdir -p /app/output /app/temp

CMD ["python3", "-u", "/app/handler.py"]

