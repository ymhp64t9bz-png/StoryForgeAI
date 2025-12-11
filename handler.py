#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 StoryForge AI Serverless v2.0 - Handler Completo
Geração completa de vídeos curtos com IA
Baseado no StoryForge AI local
"""

import runpod
import os
import sys
import logging
import tempfile
import requests
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Optional

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

print("=" * 60)
print("🔥 StoryForge AI Serverless v2.0 - Full Features")
print("=" * 60)

# ==================== IMPORTS CONDICIONAIS ====================
try:
    from moviepy.editor import (
        VideoFileClip, ImageClip, AudioFileClip,
        TextClip, CompositeVideoClip, concatenate_videoclips,
        ColorClip, CompositeAudioClip
    )
    from moviepy.video.fx import resize, fadein, fadeout
    import numpy as np
    MOVIEPY_AVAILABLE = True
    logger.info("✅ MoviePy disponível")
except ImportError as e:
    MOVIEPY_AVAILABLE = False
    logger.error(f"❌ MoviePy não disponível: {e}")

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
    logger.info("✅ PIL disponível")
except ImportError as e:
    PIL_AVAILABLE = False
    logger.error(f"❌ PIL não disponível: {e}")

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
    logger.info("✅ Edge-TTS disponível")
except ImportError as e:
    EDGE_TTS_AVAILABLE = False
    logger.warning(f"⚠️ Edge-TTS não disponível: {e}")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
    logger.info("✅ gTTS disponível")
except ImportError as e:
    GTTS_AVAILABLE = False
    logger.warning(f"⚠️ gTTS não disponível: {e}")

try:
    import boto3
    from botocore.client import Config
    
    B2_KEY_ID = os.getenv("B2_KEY_ID", "")
    B2_APP_KEY = os.getenv("B2_APP_KEY", "")
    B2_ENDPOINT = os.getenv("B2_ENDPOINT", "https://s3.us-east-005.backblazeb2.com")
    B2_BUCKET = os.getenv("B2_BUCKET_NAME", "autocortes-storage")
    
    if B2_KEY_ID and B2_APP_KEY:
        s3_client = boto3.client(
            "s3",
            endpoint_url=B2_ENDPOINT,
            aws_access_key_id=B2_KEY_ID,
            aws_secret_access_key=B2_APP_KEY,
            config=Config(signature_version="s3v4")
        )
        B2_AVAILABLE = True
        logger.info("✅ Backblaze B2 configurado")
    else:
        B2_AVAILABLE = False
        logger.warning("⚠️ B2 credentials não configuradas")
except Exception as e:
    B2_AVAILABLE = False
    logger.error(f"❌ Erro ao configurar B2: {e}")

# ==================== GERAÇÃO DE SCRIPT ====================
def generate_script_template(topic: str, style: str = "viral", duration: int = 60) -> Dict:
    """Gera script usando templates (baseado no local)"""
    
    templates = {
        'viral': {
            'title': f"🔥 {topic.upper()} - Você Precisa Ver Isso!",
            'script': f"""Você sabia que {topic}?

Isso mesmo! Hoje vou te mostrar algo incrível sobre {topic}.

Primeiro, vamos entender o básico. {topic} é algo que muitas pessoas não conhecem, mas deveria!

Agora, a parte mais interessante: existem 3 coisas essenciais que você precisa saber sobre {topic}.

Número 1: É mais comum do que você imagina.
Número 2: Pode mudar completamente sua perspectiva.
Número 3: Você pode aplicar isso hoje mesmo!

Então, o que você está esperando? Comece agora e veja os resultados!

Se você gostou, deixa o like e me segue para mais conteúdo como este!""",
            'hashtags': ['#viral', '#trending', '#fyp', '#foryou'],
            'cta': 'Segue para mais dicas incríveis!'
        },
        'educational': {
            'title': f"📚 Aprenda sobre {topic}",
            'script': f"""Hoje vamos aprender sobre {topic} de forma simples e direta.

{topic} é um assunto fascinante que todos deveriam conhecer.

Vou explicar os 3 pontos principais:

Primeiro: O que é {topic} e por que é importante.
Segundo: Como {topic} funciona na prática.
Terceiro: Como você pode aplicar {topic} no seu dia a dia.

Agora você já sabe o essencial sobre {topic}!

Quer aprender mais? Me segue para mais conteúdo educativo!""",
            'hashtags': ['#educação', '#aprendizado', '#conhecimento'],
            'cta': 'Segue para aprender mais!'
        },
        'story': {
            'title': f"✨ A História de {topic}",
            'script': f"""Era uma vez, em um lugar muito especial, onde {topic} acontecia todos os dias.

As pessoas adoravam aprender sobre {topic}, porque era mágico e transformador!

Um dia, algo incrível aconteceu. {topic} se transformou em uma grande aventura!

Todos ficaram muito felizes e aprenderam uma lição importante: {topic} é especial!

E assim, a história de {topic} continua encantando corações até hoje.

Fim! 🌟""",
            'hashtags': ['#história', '#inspiração', '#motivação'],
            'cta': 'Segue para mais histórias inspiradoras!'
        }
    }
    
    template = templates.get(style, templates['viral'])
    
    return {
        'title': template['title'],
        'script': template['script'],
        'hashtags': template['hashtags'],
        'cta': template['cta'],
        'duration': duration
    }

# ==================== GERAÇÃO DE ÁUDIO ====================
async def generate_audio_edge_tts(text: str, voice: str = "pt-BR-FranciscaNeural") -> str:
    """Gera áudio com Edge-TTS"""
    try:
        if not EDGE_TTS_AVAILABLE:
            raise Exception("Edge-TTS não disponível")
        
        output_file = TEMP_DIR / f"audio_{uuid.uuid4().hex[:8]}.mp3"
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_file))
        
        logger.info(f"✅ Áudio gerado com Edge-TTS: {output_file}")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"❌ Erro Edge-TTS: {e}")
        raise

def generate_audio_gtts(text: str, lang: str = "pt") -> str:
    """Gera áudio com gTTS (fallback)"""
    try:
        if not GTTS_AVAILABLE:
            raise Exception("gTTS não disponível")
        
        output_file = TEMP_DIR / f"audio_{uuid.uuid4().hex[:8]}.mp3"
        
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(output_file))
        
        logger.info(f"✅ Áudio gerado com gTTS: {output_file}")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"❌ Erro gTTS: {e}")
        raise

# ==================== GERAÇÃO DE IMAGENS (PLACEHOLDER) ====================
def generate_placeholder_images(num_images: int = 3) -> List[str]:
    """Gera imagens placeholder coloridas"""
    try:
        if not PIL_AVAILABLE:
            return []
        
        images = []
        colors = [
            (123, 47, 247),  # Purple
            (0, 212, 255),   # Cyan
            (255, 71, 87),   # Red
            (46, 213, 115),  # Green
            (255, 159, 64)   # Orange
        ]
        
        for i in range(num_images):
            img = Image.new('RGB', (1080, 1920), colors[i % len(colors)])
            draw = ImageDraw.Draw(img)
            
            # Adiciona texto
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            except:
                font = ImageFont.load_default()
            
            text = f"Imagem {i + 1}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (1080 - text_width) // 2
            y = (1920 - text_height) // 2
            
            draw.text((x, y), text, font=font, fill=(255, 255, 255))
            
            # Salva
            img_path = TEMP_DIR / f"img_{i}_{uuid.uuid4().hex[:8]}.png"
            img.save(img_path)
            images.append(str(img_path))
            
        logger.info(f"✅ {len(images)} imagens placeholder geradas")
        return images
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar imagens: {e}")
        return []

# ==================== COMPOSIÇÃO DE VÍDEO ====================
def create_video_from_assets(
    audio_path: str,
    image_paths: List[str],
    title: str = None,
    style: str = "viral"
) -> str:
    """Cria vídeo final com áudio, imagens e título"""
    try:
        if not MOVIEPY_AVAILABLE:
            raise Exception("MoviePy não disponível")
        
        logger.info("🎬 Compondo vídeo final...")
        
        # Carrega áudio
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        
        # Cria clips de imagens
        if image_paths:
            time_per_image = duration / len(image_paths)
            image_clips = []
            
            for i, img_path in enumerate(image_paths):
                img = ImageClip(img_path).set_duration(time_per_image)
                img = img.resize(height=1920)
                
                # Fade in/out
                if i == 0:
                    img = img.fx(fadein, 0.5)
                if i == len(image_paths) - 1:
                    img = img.fx(fadeout, 0.5)
                
                image_clips.append(img)
            
            video = concatenate_videoclips(image_clips, method="compose")
        else:
            # Background colorido se não houver imagens
            video = ColorClip(size=(1080, 1920), color=(20, 10, 40)).set_duration(duration)
        
        # Adiciona título se fornecido
        if title and PIL_AVAILABLE:
            # Cria overlay de título
            img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
            except:
                font = ImageFont.load_default()
            
            # Quebra título em linhas
            words = title.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] - bbox[0] < 1000:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Desenha título
            y_pos = 100
            for line in lines[:3]:  # Máximo 3 linhas
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x_pos = (1080 - text_width) // 2
                
                # Borda preta
                for adj_x in range(-3, 4):
                    for adj_y in range(-3, 4):
                        draw.text((x_pos + adj_x, y_pos + adj_y), line, font=font, fill=(0, 0, 0, 255))
                
                # Texto branco
                draw.text((x_pos, y_pos), line, font=font, fill=(255, 255, 255, 255))
                y_pos += 90
            
            # Converte para clip
            title_array = np.array(img)
            title_clip = ImageClip(title_array).set_duration(duration)
            
            # Composição final
            video = CompositeVideoClip([video, title_clip], size=(1080, 1920))
        
        # Adiciona áudio
        video = video.set_audio(audio)
        
        # Exporta
        output_file = OUTPUT_DIR / f"story_{uuid.uuid4().hex[:8]}.mp4"
        
        logger.info(f"🎬 Renderizando vídeo...")
        
        video.write_videofile(
            str(output_file),
            codec='libx264',
            audio_codec='aac',
            preset='fast',
            ffmpeg_params=[
                '-profile:v', 'high',
                '-level', '4.1',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart'
            ],
            verbose=False,
            logger=None
        )
        
        video.close()
        audio.close()
        
        logger.info(f"✅ Vídeo gerado: {output_file}")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar vídeo: {e}")
        raise

# ==================== UPLOAD PARA B2 ====================
def upload_to_b2(file_path: str, object_name: str = None) -> str:
    """Upload para Backblaze B2"""
    try:
        if not B2_AVAILABLE:
            logger.warning("⚠️ B2 não disponível, retornando path local")
            return file_path
        
        if object_name is None:
            object_name = f"storyforge/{os.path.basename(file_path)}"
        
        logger.info(f"📤 Uploading para B2: {object_name}")
        
        s3_client.upload_file(file_path, B2_BUCKET, object_name)
        
        # Gera URL assinada
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': B2_BUCKET, 'Key': object_name},
            ExpiresIn=3600
        )
        
        logger.info(f"✅ Upload completo: {object_name}")
        return url
        
    except Exception as e:
        logger.error(f"❌ Erro no upload B2: {e}")
        return file_path

# ==================== HANDLER PRINCIPAL ====================
def handler(event):
    """Handler principal do StoryForge AI"""
    try:
        logger.info("🚀 StoryForge Handler iniciado")
        logger.info(f"📦 Event: {event.get('id', 'N/A')}")
        
        input_data = event.get("input", {})
        
        # Modo de teste
        if input_data.get("mode") == "test":
            return {
                "status": "success",
                "message": "StoryForge AI worker funcionando!",
                "version": "2.0",
                "features": {
                    "moviepy": MOVIEPY_AVAILABLE,
                    "pil": PIL_AVAILABLE,
                    "edge_tts": EDGE_TTS_AVAILABLE,
                    "gtts": GTTS_AVAILABLE,
                    "b2": B2_AVAILABLE
                }
            }
        
        # Extrai parâmetros
        topic = input_data.get("topic")
        script_text = input_data.get("script")
        style = input_data.get("style", "viral")
        duration = input_data.get("duration", 60)
        num_images = input_data.get("num_images", 3)
        
        # Gera script se não fornecido
        if not script_text:
            if not topic:
                return {
                    "status": "error",
                    "error": "topic ou script deve ser fornecido"
                }
            
            logger.info(f"📝 Gerando script para: {topic}")
            script_data = generate_script_template(topic, style, duration)
            script_text = script_data['script']
            title = script_data['title']
        else:
            title = input_data.get("title", "StoryForge AI")
        
        # Geração de áudio
        logger.info("🎤 Gerando áudio...")
        
        if GTTS_AVAILABLE:
            audio_path = generate_audio_gtts(script_text)
        else:
            return {
                "status": "error",
                "error": "Nenhum engine de TTS disponível"
            }
        
        # Geração de imagens
        logger.info("🖼️ Gerando imagens...")
        image_paths = generate_placeholder_images(num_images)
        
        # Composição de vídeo
        video_path = create_video_from_assets(audio_path, image_paths, title, style)
        
        # Upload para B2
        video_url = upload_to_b2(video_path)
        
        # Limpeza
        try:
            os.remove(audio_path)
            for img_path in image_paths:
                os.remove(img_path)
        except:
            pass
        
        # Resultado
        result = {
            "status": "success",
            "message": "Vídeo gerado com sucesso",
            "video_url": video_url,
            "video_path": video_path,
            "title": title,
            "duration": duration
        }
        
        logger.info(f"✅ Job completo!")
        return result
        
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
    logger.info(f"📊 MoviePy: {MOVIEPY_AVAILABLE}")
    logger.info(f"📊 PIL: {PIL_AVAILABLE}")
    logger.info(f"📊 Edge-TTS: {EDGE_TTS_AVAILABLE}")
    logger.info(f"📊 gTTS: {GTTS_AVAILABLE}")
    logger.info(f"📊 B2: {B2_AVAILABLE}")
    
    runpod.serverless.start({"handler": handler})
    logger.info("✅ Worker iniciado!")
