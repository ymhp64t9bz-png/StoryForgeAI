# 🏗️ BASE IMAGE: RunPod Oficial (Pytorch 2.0.1 + Python 3.10 + CUDA 11.8)
# Esta imagem é garantida de funcionar no RunPod e já tem Python no PATH corretamente.
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04

# Metadados
LABEL maintainer="StoryForge AI Team"

# Configurações de Ambiente
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
# Define explicitamente o binário do ImageMagick para o MoviePy encontrar
ENV IMAGEMAGICK_BINARY=/usr/bin/convert

WORKDIR /app

# 📦 1. DEPENDÊNCIAS DE SISTEMA
# Instala ffmpeg, drivers de áudio (espeak) e fontes o mais cedo possível
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
# Libera o MoviePy para escrever textos nas imagens
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

# 🐍 2. DEPENDÊNCIAS PYTHON
COPY requirements.txt .
# Atualiza pip e instala requirements
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# 📥 3. CÓDIGO FONTE
COPY handler.py .

# Cria estrutura de pastas
RUN mkdir -p /app/output

# 🚀 ENTRYPOINT
# Usamos 'python3' explicitamente para evitar ambiguidade ou erro 127
CMD [ "python3", "-u", "handler.py" ]
