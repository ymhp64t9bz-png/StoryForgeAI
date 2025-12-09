# 🏗️ BASE IMAGE
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04

# Metadados
LABEL maintainer="StoryForge AI Team"

# Configurações de Ambiente
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV IMAGEMAGICK_BINARY=/usr/bin/convert
ENV PYTHONPATH=/app

WORKDIR /app

# 1. Dependências de Sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg imagemagick espeak-ng libsndfile1 fonts-noto git wget curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

# 2. Dependências Python
# Copia requirements primeiro para aproveitar cache se não mudou
COPY requirements.txt /app/requirements.txt
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir --force-reinstall -r /app/requirements.txt

# 3. Código Fonte
# Copia TUDO para garantir que b2_storage.py e handler.py venham juntos
COPY . /app/

# DEBUG: Lista arquivos e bibliotecas instaladas para auditoria no log de build
RUN echo "--- FILES IN /app ---" && ls -la /app && \
    echo "--- INSTALLED PIP PACKAGES ---" && pip list

# Cria pastas
RUN mkdir -p /app/output /app/temp

# 🚀 Start
CMD [ "python3", "-u", "/app/handler.py" ]

