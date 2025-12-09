"""
🔥 StoryForge AI - Handler de Produção (RunPod Serverless)
Pipeline: Topic -> Math Script -> Edge TTS (Async + Fallback gTTS) -> MoviePy Video -> B2 Upload
Versão: 100% Async Native
"""

import runpod
import os
import asyncio
import logging
import time
import random
import edge_tts
from gtts import gTTS
import b2_storage  # Módulo B2 Local

# Imports de Mídia
from moviepy.editor import (
    AudioFileClip, TextClip, ColorClip, CompositeVideoClip
)
from moviepy.config import change_settings

# Configurações
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StoryForge-Cloud")

# Diretórios
OUTPUT_DIR = "/app/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------- #
#                                LÓGICA DE NEGÓCIO                             #
# ---------------------------------------------------------------------------- #

def generate_script_logic(topic, duration_seconds):
    """Gera roteiro (Síncrono/CPU Bound)."""
    target_words = int(duration_seconds * 2.5)
    logger.info(f"📝 Topic: {topic} | Duração: {duration_seconds}s | Alvo: {target_words} palavras")
    
    intro = f"Hoje vamos falar sobre {topic}. "
    fillers = [
        "Isso é algo que muda tudo.", "A ciência por trás disso é fascinante.",
        f"Muitos não sabem a verdade sobre {topic}.", "Imagine as possibilidades.",
        "Os detalhes são surpreendentes.", "Isso impacta nossa vida diariamente."
    ]
    
    text = intro
    while len(text.split()) < target_words:
        text += random.choice(fillers) + " "
        
    words = text.split()[:target_words]
    final_text = " ".join(words)
    return final_text

async def generate_voice_pure_async(text, voice):
    """Gera áudio MP3 (Edge TTS -> gTTS)."""
    filename = f"audio_{int(time.time())}_{random.randint(1000,9999)}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        logger.info(f"🎙️ Tentando Edge TTS ({voice})...")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)
    except Exception as e:
        logger.warning(f"⚠️ Edge TTS falhou ({e}). Tentando fallback gTTS...")
        try:
            tts = gTTS(text=text, lang='pt')
            tts.save(filepath)
        except Exception as e_ft:
            logger.error(f"❌ Falha total no áudio: {e_ft}")
            raise e_ft
            
    return filepath

def generate_video_render(audio_path, topic):
    """Renderiza MP4 (Síncrono/CPU Bound)."""
    logger.info("🎬 Renderizando vídeo...")
    filename = f"storyforge_{int(time.time())}_{random.randint(1000,9999)}.mp4"
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    if not os.path.exists(audio_path):
        raise ValueError("Arquivo de áudio não encontrado")

    audio = AudioFileClip(audio_path)
    dur = audio.duration
    
    bg = ColorClip(size=(1080, 1920), color=(15, 20, 25), duration=dur)
    
    try:
        font_name = 'DejaVu-Sans-Bold'
    except:
        font_name = 'Arial'
        
    txt = TextClip(
        topic.upper(), 
        fontsize=80, 
        color='white', 
        font=font_name, 
        size=(900, None), 
        method='caption'
    ).set_position('center').set_duration(dur)
    
    final = CompositeVideoClip([bg, txt]).set_audio(audio)
    
    final.write_videofile(
        output_path, 
        fps=24, 
        codec='libx264', 
        audio_codec='aac',
        preset='ultrafast',
        threads=4,
        logger=None
    )
    
    return output_path

# ---------------------------------------------------------------------------- #
#                                RUNPOD HANDLER                                #
# ---------------------------------------------------------------------------- #

async def handler(job):
    """
    Handler com Upload B2 Integrado.
    """
    job_input = job.get("input", {})
    
    topic = job_input.get("topic", "Tecnologia")
    duration = int(job_input.get("duration", 30))
    voice = job_input.get("voice", "pt-BR-AntonioNeural")
    
    try:
        logger.info(f"🚀 Job Start: {topic}")
        
        # 1. Pipeline de Geração
        script = generate_script_logic(topic, duration)
        audio_path = await generate_voice_pure_async(script, voice)
        video_path = generate_video_render(audio_path, topic)
        
        # 2. Upload para B2 (Seguro)
        logger.info("☁️ Iniciando Upload Seguro para B2...")
        file_name = f"storyforge/{os.path.basename(video_path)}"
        
        # Upload
        uploaded_key = b2_storage.upload_file(video_path, file_name)
        
        response_payload = {
            "status": "success",
            "script_word_count": len(script.split()),
            "duration": duration
        }

        if uploaded_key:
            # Gerar Signed URL para acesso imediato (opcional, válido por 1h)
            signed_url = b2_storage.generate_signed_download_url(uploaded_key, expires_in=3600)
            
            response_payload["b2_key"] = uploaded_key
            response_payload["signed_url"] = signed_url
            response_payload["video_path"] = signed_url # Para compatibilidade com frontend antigo
            
            logger.info(f"✅ B2 Upload Sucesso: {uploaded_key}")
        else:
            # Fallback: Retorna path local (se volume tiver montado)
            logger.warning("⚠️ B2 Upload falhou. Retornando path local.")
            response_payload["video_path"] = video_path

        return response_payload
        
    except Exception as e:
        logger.error(f"❌ Erro Fatal no Job: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
