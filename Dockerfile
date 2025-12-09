# 🏗️ BASE IMAGE: RunPod Oficial (Pytorch 2.0.1 + Python 3.10 + CUDA 11.8)
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04

# Metadados
LABEL maintainer="StoryForge AI Team"

# Configurações de Ambiente
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV IMAGEMAGICK_BINARY=/usr/bin/convert
ENV PYTHONPATH=/app

WORKDIR /app

# 📦 1. DEPENDÊNCIAS DE SISTEMA
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    imagemagick \
    espeak-ng \
    libsndfile1 \
    fonts-noto \
    fonts-noto-color-emoji \
    fonts-liberation \
    git \
    wget \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 🛠️ CORREÇÃO DE SEGURANÇA DO IMAGEMAGICK
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

# 🐍 2. DEPENDÊNCIAS PYTHON
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r /app/requirements.txt

# 📥 3. CÓDIGO FONTE (Copia tudo da pasta atual para /app)
COPY . /app/

# Cria estrutura de pastas
RUN mkdir -p /app/output /app/temp

# 🚀 ENTRYPOINT
# Usa caminho absoluto para garantir
CMD [ "python3", "-u", "/app/handler.py" ]
