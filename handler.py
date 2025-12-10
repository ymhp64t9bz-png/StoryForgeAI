import runpod
import os
import uuid
import logging
import boto3
from botocore.client import Config

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import numpy as np

# ============================
# CONFIGURAÇÃO
# ============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StoryForge")

TEMP_DIR = "/app/temp"
OUT_DIR = "/app/output"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

B2_ENDPOINT = os.getenv("B2_ENDPOINT_URL", "https://s3.us-east-005.backblazeb2.com")
B2_BUCKET = os.getenv("B2_BUCKET_NAME")
B2_KEY = os.getenv("B2_KEY_ID")
B2_SECRET = os.getenv("B2_APPLICATION_KEY")


# ============================
# FUNÇÃO: CLIENTE S3 B2
# ============================
def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=B2_ENDPOINT,
        aws_access_key_id=B2_KEY,
        aws_secret_access_key=B2_SECRET,
        config=Config(signature_version="s3v4")
    )


# ============================
# FUNÇÃO: UPLOAD + URL ASSINADA
# ============================
def upload_to_b2(local_file, file_name):
    s3 = get_s3()

    logger.info(f"📤 Enviando vídeo ao B2: {file_name}")
    s3.upload_file(local_file, B2_BUCKET, file_name)

    logger.info("🔐 Gerando URL assinada...")
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": B2_BUCKET, "Key": file_name},
        ExpiresIn=3600 * 24  # 24h
    )

    return url


# ============================
# FUNÇÃO: GERAR SLIDES (IMAGENS)
# ============================
def generate_slides(text_parts):
    slides = []

    for i, text in enumerate(text_parts):
        img_path = os.path.join(TEMP_DIR, f"slide_{i}.png")

        img = Image.new("RGB", (1080, 1920), color="#0d0d0d")
        draw = ImageDraw.Draw(img)

        # Fonte padrão do Pillow
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)

        # Texto centralizado
        box = draw.textbbox((0, 0), text, font=font)
        w = box[2] - box[0]
        h = box[3] - box[1]

        draw.text(
            ((1080 - w) / 2, (1920 - h) / 2),
            text,
            fill="#ffffff",
            font=font
        )

        img.save(img_path)
        slides.append(img_path)

    return slides


# ============================
# FUNÇÃO: TTS
# ============================
def generate_tts(text):
    tts_path = os.path.join(TEMP_DIR, "tts.mp3")
    tts = gTTS(text=text, lang="pt")
    tts.save(tts_path)
    return tts_path


# ============================
# FUNÇÃO: MONTAR VÍDEO
# ============================
def create_video(slides, audio_path):
    audio = AudioFileClip(audio_path)
    duration_per_slide = audio.duration / len(slides)

    clips = []
    for slide in slides:
        img_clip = ImageClip(slide).set_duration(duration_per_slide)
        clips.append(img_clip)

    final = concatenate_videoclips(clips)
    final = final.set_audio(audio)

    out_path = os.path.join(OUT_DIR, f"storyforge_{uuid.uuid4()}.mp4")

    final.write_videofile(
        out_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        logger=None
    )

    audio.close()
    return out_path


# ============================
# HANDLER PRINCIPAL
# ============================
async def handler(job):
    """
    INPUT esperado:
    {
        "script": "texto gerado pela IA"
    }
    """
    try:
        data = job["input"]
        script = data.get("script")

        if not script:
            return {"error": "Nenhum script fornecido."}

        logger.info("📝 Script recebido. Iniciando StoryForge...")

        # Divide o script em pedaços curtos
        parts = [p.strip() for p in script.split("\n") if p.strip()]

        # 1) Criar imagens
        slides = generate_slides(parts)

        # 2) Criar TTS
        tts_path = generate_tts(script)

        # 3) Renderizar vídeo final
        video_path = create_video(slides, tts_path)

        # 4) Upload para B2
        file_name = f"storyforge/{os.path.basename(video_path)}"
        signed_url = upload_to_b2(video_path, file_name)

        # 5) Limpeza
        for f in slides:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(tts_path):
            os.remove(tts_path)
        if os.path.exists(video_path):
            os.remove(video_path)

        return {
            "status": "success",
            "video_url": signed_url
        }

    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        return {"error": str(e)}


# ============================
# RUNPOD
# ============================
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
