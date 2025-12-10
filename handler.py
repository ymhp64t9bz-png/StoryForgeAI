"""
🔥 StoryForge AI — Cloud Handler (Backblaze B2 Integration)
Pipeline: Gera vídeo → Salva no TEMP → Faz upload B2 → Retorna Signed URL
"""

import os
import uuid
import logging
import runpod
import b2_storage
from moviepy.editor import VideoFileClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StoryForge-Cloud")

OUTPUT_DIR = "/app/output"
TEMP_DIR = "/app/temp"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


def render_story_video(text_content: str, duration: int):
    """
    Simulação do motor de render do StoryForge AI.
    Aqui você vai colocar futuramente os blocos de:
    - geração de vídeo
    - voice-over
    - edição
    """
    filename = f"storyforge_{uuid.uuid4()}.mp4"
    output_path = os.path.join(OUTPUT_DIR, filename)

    # *** Aqui entra seu pipeline real ***
    clip = VideoFileClip("base.mp4").subclip(0, min(10, duration))
    clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    clip.close()

    return output_path


async def handler(job):
    job_input = job.get("input", {})

    topic = job_input.get("topic")
    duration = job_input.get("duration", 60)
    if not topic:
        return {"status": "error", "error": "Missing topic"}

    logger.info(f"🚀 Renderizando Story Forge: {topic}")

    try:
        # 1 — Renderização
        local_video = render_story_video(topic, duration)

        # 2 — Upload para Backblaze B2
        file_name = f"storyforge/{os.path.basename(local_video)}"
        b2_storage.upload_file(local_video, file_name)

        # 3 — URL Assinada
        signed_url = b2_storage.generate_signed_download_url(file_name)

        # 4 — Limpeza
        if os.path.exists(local_video):
            os.remove(local_video)

        return {
            "status": "success",
            "file": file_name,
            "download_url": signed_url
        }

    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
