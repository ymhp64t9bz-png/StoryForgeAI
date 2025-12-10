FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# ==========================================
# SISTEMA - Dependências essenciais
# ==========================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    imagemagick \
    libsndfile1 \
    git \
    wget \
    curl \
    libgl1 \
    fonts-dejavu-core \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Liberar ImageMagick (correção obrigatória)
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

# ==========================================
# PYTHON - Instala dependências do StoryForge
# ==========================================
COPY requirements.txt /app/requirements.txt

RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir --force-reinstall -r /app/requirements.txt

# ==========================================
# APLICATIVO
# ==========================================
COPY . /app/

RUN mkdir -p /app/output /app/temp

CMD ["python3", "-u", "/app/handler.py"]

