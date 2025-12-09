"""
✂️ AnimeCut Cloud - Handler de Produção
Pipeline: Download -> Detecção de Cenas (ContentDetector) -> Filtro Viral -> Upload B2
"""

import runpod
import os
import logging
import requests
import uuid
import b2_storage
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from moviepy.editor import VideoFileClip

# Configuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnimeCut-Cloud")

OUTPUT_DIR = "/app/output"
TEMP_DIR = "/app/temp"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def download_video(url):
    """Baixa vídeo da URL para temp"""
    local_filename = os.path.join(TEMP_DIR, f"source_{uuid.uuid4()}.mp4")
    logger.info(f"⬇️ Baixando vídeo: {url}")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

def detect_scenes(video_path, threshold=27.0):
    """Usa PySceneDetect para encontrar cortes"""
    logger.info("🔍 Detectando cenas...")
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    
    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)
    
    scene_list = scene_manager.get_scene_list()
    logger.info(f"✅ Encontradas {len(scene_list)} cenas.")
    return scene_list

def process_anime_cuts(video_path, scene_list, min_duration=60, max_duration=180):
    """Corta o vídeo nas cenas detectadas (Alvo: 60s a 180s)"""
    clips_generated = []
    
    try:
        video = VideoFileClip(video_path)
        
        for i, scene in enumerate(scene_list):
            start_time = scene[0].get_seconds()
            end_time = scene[1].get_seconds()
            duration = end_time - start_time
            
            # Filtro de duração atualizado (60s - 180s)
            if duration < min_duration or duration > max_duration:
                continue
                
            logger.info(f"✂️ Processando Cena {i}: {duration:.1f}s")
            
            # Corta
            clip = video.subclip(start_time, end_time)
            
            # Opcional: Resize para Vertical se não for (9:16)
            # Para Anime, geralmente mantemos 16:9 ou fazemos crop. 
            # Aqui mantemos original para qualidade máxima.
            
            output_filename = f"animecut_{uuid.uuid4()}_scene{i}.mp4"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                preset='fast',
                logger=None
            )
            clips_generated.append(output_path)
            
            # Limite de segurança para não gerar 100 clips num job
            if len(clips_generated) >= 5: 
                break
                
        video.close()
        return clips_generated
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento de vídeo: {e}")
        return []

async def handler(job):
    job_input = job.get("input", {})
    video_url = job_input.get("video_url")
    min_dur = job_input.get("min_duration", 60) # Padrão atualizado para 60s
    
    if not video_url:
        return {"status": "error", "error": "No video_url provided"}
    
    try:
        # 1. Download
        source_path = download_video(video_url)
        
        # 2. Detecção
        scenes = detect_scenes(source_path)
        if not scenes:
             return {"status": "error", "error": "No scenes detected"}
             
        # 3. Processamento & Corte
        cut_paths = process_anime_cuts(source_path, scenes, min_duration=min_dur)
        
        # 4. Upload B2 (Multi-file)
        results = []
        for path in cut_paths:
            file_name = f"animecut/{os.path.basename(path)}"
            if b2_storage.upload_file(path, file_name):
                url = b2_storage.generate_signed_download_url(file_name)
                results.append(url)
        
        # Limpeza
        if os.path.exists(source_path): os.remove(source_path)
        
        return {
            "status": "success",
            "total_scenes": len(scenes),
            "generated_clips": len(results),
            "download_urls": results
        }

    except Exception as e:
        logger.error(f"❌ Erro Fatal: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
