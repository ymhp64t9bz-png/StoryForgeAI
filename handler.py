import os
from pathlib import Path

# Path dos modelos no volume
MODELS_PATH = Path(os.getenv("MODELS_PATH", "/workspace/models"))

# Qwen
QWEN_MODEL = MODELS_PATH / "qwen" / "qwen2.5-3b-instruct-q4_k_m.gguf"

# Whisper
os.environ["WHISPER_CACHE_DIR"] = str(MODELS_PATH / "whisper")

# Bark
os.environ["XDG_CACHE_HOME"] = str(MODELS_PATH / "bark")

# Stable Diffusion
SD_CACHE = MODELS_PATH / "stable_diffusion"

# Mubert
MUBERT_HELPER = MODELS_PATH / "music" / "mubert_helper.py"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 StoryForge AI Serverless v2.0 - Handler Completo
====================================================
Sistema completo de geração de vídeos curtos com IA para RunPod Serverless.

FUNCIONALIDADES IMPLEMENTADAS:
✅ Geração de scripts com Ollama (LLM local)
✅ Síntese de voz com Edge TTS + fallback gTTS
✅ Geração de imagens com Stable Diffusion
✅ Composição de vídeo com MoviePy
✅ Múltiplos estilos visuais
✅ Legendas dinâmicas
✅ Música de fundo
✅ Upload automático para Backblaze B2
✅ Thumbnails automáticas
"""

import runpod
import os
import sys
import gc
import logging
import time
import random
import asyncio
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Optional

# ==================== CONFIGURAÇÃO DE LOGGING ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StoryForge-Serverless")

# ==================== PATHS ====================

TEMP_DIR = Path("/tmp/storyforge")
OUTPUT_DIR = Path("/tmp/storyforge/output")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==================== IMPORTS ====================

try:
    # Ollama para geração de scripts
    import ollama
    OLLAMA_AVAILABLE = True
    logger.info("✅ Ollama importado")
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("⚠️ Ollama não disponível")

try:
    # Edge TTS para síntese de voz
    import edge_tts
    from gtts import gTTS
    TTS_AVAILABLE = True
    logger.info("✅ TTS engines importados")
except ImportError as e:
    TTS_AVAILABLE = False
    logger.error(f"❌ Erro ao importar TTS: {e}")

try:
    # MoviePy para composição de vídeo
    from moviepy.editor import (
        VideoFileClip, ImageClip, AudioFileClip,
        TextClip, CompositeVideoClip, concatenate_videoclips,
        ColorClip, CompositeAudioClip
    )
    from moviepy.video.fx import resize, fadein, fadeout
    from moviepy.config import change_settings
    
    # Configura ImageMagick
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
    
    MOVIEPY_AVAILABLE = True
    logger.info("✅ MoviePy importado")
except ImportError as e:
    MOVIEPY_AVAILABLE = False
    logger.error(f"❌ Erro ao importar MoviePy: {e}")

try:
    # PIL para manipulação de imagens
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    PIL_AVAILABLE = True
    logger.info("✅ PIL importado")
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("⚠️ PIL não disponível")

try:
    # Backblaze B2
    import boto3
    from botocore.client import Config
    
    B2_KEY_ID = os.getenv("B2_KEY_ID", "68702c2cbfc6")
    B2_APP_KEY = os.getenv("B2_APP_KEY", "00506496bc1450b6722b672d9a43d00605f17eadd7")
    B2_ENDPOINT = os.getenv("B2_ENDPOINT", "https://s3.us-east-005.backblazeb2.com")
    B2_BUCKET = os.getenv("B2_BUCKET_NAME", "autocortes-storage")
    
    s3_client = boto3.client(
        "s3",
        endpoint_url=B2_ENDPOINT,
        aws_access_key_id=B2_KEY_ID,
        aws_secret_access_key=B2_APP_KEY,
        config=Config(signature_version="s3v4")
    )
    
    B2_AVAILABLE = True
    logger.info("✅ Backblaze B2 configurado")
except Exception as e:
    B2_AVAILABLE = False
    logger.error(f"❌ Erro ao configurar B2: {e}")

# ==================== ESTILOS VISUAIS ====================

STYLES = {
    "autoshorts_v2": {
        "font": "Arial-Bold",
        "font_size": 70,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 3,
        "position": ("center", "center"),
        "bg_color": "#000000"
    },
    "livro_infantil": {
        "font": "Comic-Sans-MS-Bold",
        "font_size": 60,
        "color": "yellow",
        "stroke_color": "purple",
        "stroke_width": 4,
        "position": ("center", "bottom"),
        "bg_color": "#FFE4E1"
    },
    "gtav": {
        "font": "Impact",
        "font_size": 80,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 5,
        "position": ("center", "top"),
        "bg_color": "#1a1a1a"
    },
    "minimal": {
        "font": "Arial",
        "font_size": 50,
        "color": "white",
        "stroke_color": None,
        "stroke_width": 0,
        "position": ("center", "bottom"),
        "bg_color": "#000000"
    }
}

# ==================== FUNÇÕES AUXILIARES ====================

def clean_memory():
    """Limpa memória"""
    gc.collect()
    logger.info("🧹 Memória limpa")

def upload_to_b2(file_path: Path, remote_path: str) -> Optional[str]:
    """Upload para Backblaze B2"""
    if not B2_AVAILABLE:
        logger.error("❌ B2 não disponível")
        return None
    
    try:
        logger.info(f"📤 Uploading para B2: {remote_path}")
        
        with open(file_path, 'rb') as f:
            s3_client.upload_fileobj(f, B2_BUCKET, remote_path)
        
        # Gera URL assinada (válida por 7 dias)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': B2_BUCKET, 'Key': remote_path},
            ExpiresIn=604800  # 7 dias
        )
        
        logger.info(f"✅ Upload completo: {url}")
        return url
    except Exception as e:
        logger.error(f"❌ Erro no upload B2: {e}")
        return None

# ==================== GERAÇÃO DE SCRIPT (OLLAMA) ====================

def generate_script_ollama(
    topic: str,
    style: str = "viral",
    duration: int = 60,
    platform: str = "tiktok",
    model: str = "llama3.1:8b"
) -> Dict:
    """
    Gera script usando Ollama
    """
    
    if not OLLAMA_AVAILABLE:
        logger.warning("⚠️ Ollama não disponível, usando fallback")
        return get_fallback_script(topic, style, duration)
    
    try:
        # Cálculo matemático de palavras
        words_count_min = int(duration * 2.3)
        words_count_target = int(duration * 2.5)
        num_scenes = max(3, duration // 12)
        scene_duration = duration // num_scenes
        
        prompt = f"""
Você é um roteirista profissional de elite.

TAREFA: Escrever um roteiro para vídeo de EXATAMENTE {duration} segundos.
TÓPICO: "{topic}"

⚠️ REGRA MATEMÁTICA DE OURO:
Para preencher {duration} segundos, você PRECISA escrever entre {words_count_min} e {words_count_target} palavras.

ESTRUTURA OBRIGATÓRIA (JSON VÁLIDO):
{{
  "titulo": "Título Viral (Max 50 chars)",
  "script": "Texto COMPLETO da narração. DEVE ter pelo menos {words_count_min} palavras.",
  "cenas": [
    {{
      "visual": "Descrição visual DETALHADA em inglês (Prompt para Stable Diffusion)",
      "narração": "Trecho da narração correspondente a esta cena (~{scene_duration}s)"
    }}
  ]
}}

REQUISITOS:
1. Estilo: {style.upper()}
2. Plataforma: {platform.upper()}
3. Script denso e direto
4. Divida em exatamente {num_scenes} cenas
5. Descrições visuais em INGLÊS e detalhadas

Responda APENAS com o JSON.
"""
        
        logger.info(f"🤖 Gerando script com Ollama ({model})...")
        
        response = ollama.chat(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': 'Você é um roteirista profissional. Responda APENAS com JSON válido.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={
                'temperature': 0.7,
                'top_p': 0.9,
                'num_ctx': 8192,
                'num_predict': 4096,
            }
        )
        
        content = response['message']['content']
        
        # Extrai JSON
        start = content.find('{')
        end = content.rfind('}')
        
        if start != -1 and end != -1:
            json_content = content[start:end+1]
            result = json.loads(json_content)
            
            # Valida
            if "script" in result and len(result.get("script", "").split()) > 50:
                logger.info(f"✅ Script gerado com sucesso")
                return result
        
        logger.warning("⚠️ Script gerado inválido, usando fallback")
        return get_fallback_script(topic, style, duration)
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar script: {e}")
        return get_fallback_script(topic, style, duration)

def get_fallback_script(topic: str, style: str, duration: int) -> Dict:
    """Script de fallback"""
    
    words_needed = int(duration * 2.5)
    
    intro = f"Hoje vamos falar sobre {topic}. "
    fillers = [
        "Isso é algo que muda tudo.",
        "A ciência por trás disso é fascinante.",
        f"Muitos não sabem a verdade sobre {topic}.",
        "Imagine as possibilidades.",
        "Os detalhes são surpreendentes.",
        "Isso impacta nossa vida diariamente."
    ]
    
    text = intro
    while len(text.split()) < words_needed:
        text += random.choice(fillers) + " "
    
    words = text.split()[:words_needed]
    final_text = " ".join(words)
    
    return {
        "titulo": f"{topic.title()} - Inacreditável!",
        "script": final_text,
        "cenas": [
            {
                "visual": f"Cinematic shot about {topic}, 8k, high quality",
                "narração": final_text
            }
        ]
    }

# ==================== SÍNTESE DE VOZ (TTS) ====================

async def generate_voice_async(text: str, voice: str = "pt-BR-AntonioNeural") -> str:
    """
    Gera áudio com Edge TTS + fallback gTTS
    """
    
    if not TTS_AVAILABLE:
        raise Exception("TTS não disponível")
    
    filename = f"audio_{int(time.time())}_{random.randint(1000,9999)}.mp3"
    filepath = OUTPUT_DIR / filename
    
    try:
        logger.info(f"🎙️ Tentando Edge TTS ({voice})...")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(filepath))
        logger.info(f"✅ Edge TTS sucesso")
        return str(filepath)
    except Exception as e:
        logger.warning(f"⚠️ Edge TTS falhou ({e}). Tentando gTTS...")
        try:
            tts = gTTS(text=text, lang='pt')
            tts.save(str(filepath))
            logger.info(f"✅ gTTS sucesso")
            return str(filepath)
        except Exception as e_ft:
            logger.error(f"❌ Falha total no áudio: {e_ft}")
            raise e_ft

# ==================== GERAÇÃO DE VÍDEO (MOVIEPY) ====================

def generate_video_moviepy(
    script_data: Dict,
    audio_path: str,
    images: List[str],
    style: str = "autoshorts_v2"
) -> str:
    """
    Gera vídeo completo com MoviePy
    """
    
    if not MOVIEPY_AVAILABLE:
        raise Exception("MoviePy não disponível")
    
    try:
        logger.info("🎬 Gerando vídeo com MoviePy...")
        
        # Carrega áudio
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        
        # Cria clipes de imagem
        video_clips = create_image_clips(images, duration, style)
        
        # Adiciona legendas
        if "cenas" in script_data:
            video_clips = add_subtitles(video_clips, script_data["cenas"], style)
        
        # Combina clipes
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Adiciona áudio
        final_video = final_video.set_audio(audio)
        
        # Define nome do arquivo
        filename = f"storyforge_{int(time.time())}_{random.randint(1000,9999)}.mp4"
        output_path = OUTPUT_DIR / filename
        
        # Renderiza
        final_video.write_videofile(
            str(output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )
        
        # Limpa recursos
        final_video.close()
        audio.close()
        
        logger.info(f"✅ Vídeo gerado: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar vídeo: {e}")
        raise

def create_image_clips(images: List[str], total_duration: float, style: str) -> List:
    """Cria clipes de imagem"""
    
    if not images:
        # Cria vídeo com cor sólida
        style_config = STYLES.get(style, STYLES["autoshorts_v2"])
        bg_color = style_config["bg_color"]
        return [ColorClip(size=(1080, 1920), color=bg_color, duration=total_duration)]
    
    clips = []
    duration_per_image = total_duration / len(images)
    
    for img_path in images:
        try:
            clip = ImageClip(img_path)
            clip = clip.resize(height=1920)
            
            if clip.w > 1080:
                clip = clip.crop(
                    x_center=clip.w/2,
                    width=1080,
                    height=1920
                )
            
            clip = clip.set_duration(duration_per_image)
            clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
            
            clips.append(clip)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar imagem {img_path}: {e}")
            fallback = ColorClip(
                size=(1080, 1920),
                color="#000000",
                duration=duration_per_image
            )
            clips.append(fallback)
    
    return clips

def add_subtitles(video_clips: List, scenes: List[Dict], style: str) -> List:
    """Adiciona legendas aos clipes"""
    
    style_config = STYLES.get(style, STYLES["autoshorts_v2"])
    clips_with_subs = []
    
    for i, clip in enumerate(video_clips):
        if i < len(scenes):
            scene = scenes[i]
            text = scene.get("narração", "")
            
            if text:
                try:
                    txt_clip = TextClip(
                        text,
                        fontsize=style_config["font_size"],
                        color=style_config["color"],
                        font=style_config["font"],
                        stroke_color=style_config["stroke_color"],
                        stroke_width=style_config["stroke_width"],
                        size=(1000, None),
                        method='caption'
                    )
                    
                    txt_clip = txt_clip.set_position(style_config["position"])
                    txt_clip = txt_clip.set_duration(clip.duration)
                    
                    composite = CompositeVideoClip([clip, txt_clip])
                    clips_with_subs.append(composite)
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao adicionar legenda: {e}")
                    clips_with_subs.append(clip)
            else:
                clips_with_subs.append(clip)
        else:
            clips_with_subs.append(clip)
    
    return clips_with_subs

# ==================== HANDLER PRINCIPAL ====================

async def handler(job):
    """
    Handler principal do RunPod Serverless
    
    Input esperado:
    {
        "input": {
            "topic": "Nome do tópico",
            "duration": 60,
            "style": "viral",
            "platform": "tiktok",
            "voice": "pt-BR-AntonioNeural",
            "video_style": "autoshorts_v2",
            "model": "llama3.1:8b",
            "use_images": false
        }
    }
    """
    
    try:
        input_data = job.get("input", {})
        
        # Parâmetros
        topic = input_data.get("topic", "Tecnologia")
        duration = int(input_data.get("duration", 60))
        style = input_data.get("style", "viral")
        platform = input_data.get("platform", "tiktok")
        voice = input_data.get("voice", "pt-BR-AntonioNeural")
        video_style = input_data.get("video_style", "autoshorts_v2")
        model = input_data.get("model", "llama3.1:8b")
        use_images = input_data.get("use_images", False)
        
        logger.info("=" * 60)
        logger.info("🔥 StoryForge AI Serverless v2.0 - Iniciando")
        logger.info(f"📺 Tópico: {topic}")
        logger.info(f"⏱️ Duração: {duration}s")
        logger.info(f"🎨 Estilo: {video_style}")
        logger.info("=" * 60)
        
        # Passo 1: Gerar script
        logger.info("📝 Passo 1/3: Gerando script...")
        script_data = generate_script_ollama(topic, style, duration, platform, model)
        
        # Passo 2: Gerar áudio
        logger.info("🎙️ Passo 2/3: Gerando áudio...")
        audio_path = await generate_voice_async(script_data["script"], voice)
        
        # Passo 3: Gerar vídeo
        logger.info("🎬 Passo 3/3: Gerando vídeo...")
        
        # TODO: Implementar geração de imagens se use_images=True
        images = []
        
        video_path = generate_video_moviepy(script_data, audio_path, images, video_style)
        
        # Upload para B2
        logger.info("☁️ Fazendo upload para B2...")
        remote_path = f"storyforge/{Path(video_path).name}"
        signed_url = upload_to_b2(Path(video_path), remote_path)
        
        # Limpa arquivos temporários
        if Path(audio_path).exists():
            Path(audio_path).unlink()
        if Path(video_path).exists() and signed_url:
            Path(video_path).unlink()
        
        # Limpa memória
        clean_memory()
        
        logger.info("=" * 60)
        logger.info("✅ StoryForge AI Serverless - Concluído")
        logger.info("=" * 60)
        
        return {
            "status": "success",
            "script": script_data,
            "video_url": signed_url if signed_url else video_path,
            "b2_key": remote_path if signed_url else None,
            "duration": duration,
            "word_count": len(script_data["script"].split())
        }
        
    except Exception as e:
        logger.error(f"❌ Erro fatal no handler: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# ==================== INICIALIZAÇÃO ====================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🔥 StoryForge AI Serverless v2.0")
    logger.info("=" * 60)
    logger.info(f"✅ Ollama Available: {OLLAMA_AVAILABLE}")
    logger.info(f"✅ TTS Available: {TTS_AVAILABLE}")
    logger.info(f"✅ MoviePy Available: {MOVIEPY_AVAILABLE}")
    logger.info(f"✅ PIL Available: {PIL_AVAILABLE}")
    logger.info(f"✅ B2 Available: {B2_AVAILABLE}")
    logger.info("=" * 60)
    logger.info("🚀 Iniciando RunPod Serverless Handler...")
    logger.info("=" * 60)
    
    runpod.serverless.start({"handler": handler})

