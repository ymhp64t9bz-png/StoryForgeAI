# -*- coding: utf-8 -*-
"""
🔥 StoryForge AI Serverless v2.0 - Handler Simplificado
Versão funcional para teste de dependências
"""

import runpod
import os
import sys
import logging
from pathlib import Path

# ==================== CONFIGURAÇÃO ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StoryForge")

# Diretórios
TEMP_DIR = Path("/tmp/storyforge")
OUTPUT_DIR = Path("/tmp/storyforge/output")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==================== VERIFICAR DEPENDÊNCIAS ====================
def check_dependencies():
    """Verifica quais dependências estão disponíveis"""
    deps = {}
    
    try:
        from moviepy.editor import VideoFileClip
        deps['moviepy'] = True
        logger.info("✅ MoviePy disponível")
    except ImportError as e:
        deps['moviepy'] = False
        logger.error(f"❌ MoviePy não disponível: {e}")
    
    try:
        import edge_tts
        deps['edge_tts'] = True
        logger.info("✅ Edge-TTS disponível")
    except ImportError as e:
        deps['edge_tts'] = False
        logger.error(f"❌ Edge-TTS não disponível: {e}")
    
    try:
        from gtts import gTTS
        deps['gtts'] = True
        logger.info("✅ gTTS disponível")
    except ImportError as e:
        deps['gtts'] = False
        logger.error(f"❌ gTTS não disponível: {e}")
    
    try:
        import boto3
        deps['boto3'] = True
        logger.info("✅ Boto3 disponível")
    except ImportError as e:
        deps['boto3'] = False
        logger.error(f"❌ Boto3 não disponível: {e}")
    
    try:
        from PIL import Image
        deps['pil'] = True
        logger.info("✅ PIL disponível")
    except ImportError as e:
        deps['pil'] = False
        logger.error(f"❌ PIL não disponível: {e}")
    
    try:
        import numpy
        deps['numpy'] = True
        logger.info("✅ Numpy disponível")
    except ImportError as e:
        deps['numpy'] = False
        logger.error(f"❌ Numpy não disponível: {e}")
    
    return deps

# ==================== HANDLER ====================
def handler(event):
    """
    Handler principal do StoryForge AI Serverless
    
    Payload esperado:
    {
        "input": {
            "mode": "test"
        }
    }
    """
    try:
        logger.info("🚀 StoryForge AI Serverless v2.0 iniciado")
        logger.info(f"📦 Event recebido: {event}")
        
        # Verifica dependências
        deps = check_dependencies()
        
        # Extrai input
        input_data = event.get("input", {})
        mode = input_data.get("mode", "test")
        
        # Modo de teste
        if mode == "test":
            return {
                "status": "success",
                "message": "StoryForge AI worker está funcionando!",
                "dependencies": deps,
                "python_version": sys.version,
                "temp_dir": str(TEMP_DIR),
                "output_dir": str(OUTPUT_DIR),
                "env_vars": {
                    "MODELS_PATH": os.getenv("MODELS_PATH", "not set"),
                    "B2_BUCKET_NAME": os.getenv("B2_BUCKET_NAME", "not set")
                }
            }
        
        else:
            return {
                "status": "error",
                "message": f"Modo '{mode}' não reconhecido. Use: test"
            }
    
    except Exception as e:
        logger.error(f"❌ Erro no handler: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "type": type(e).__name__
        }

# ==================== INICIALIZAÇÃO ====================
if __name__ == "__main__":
    logger.info("🔥 Iniciando StoryForge AI Serverless Worker...")
    
    # Verifica dependências na inicialização
    deps = check_dependencies()
    
    # Inicia o worker RunPod
    runpod.serverless.start({"handler": handler})
