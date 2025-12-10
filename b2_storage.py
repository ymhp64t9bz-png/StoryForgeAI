"""
🔒 B2 Storage Module - Integração Backblaze B2 (S3-Compatible)
Gerencia uploads, downloads e URLs assinadas usando boto3 (S3v4).
"""

import os
import logging
import boto3
from botocore.client import Config
from pathlib import Path
from typing import Optional

logger = logging.getLogger("B2Storage")

# ==================== CONFIGURAÇÃO ====================

B2_KEY_ID = os.getenv("B2_KEY_ID", "68702c2cbfc6")
B2_APP_KEY = os.getenv("B2_APP_KEY", "00506496bc1450b6722b672d9a43d00605f17eadd7")
B2_ENDPOINT = os.getenv("B2_ENDPOINT", "https://s3.us-east-005.backblazeb2.com")
B2_BUCKET = os.getenv("B2_BUCKET_NAME", "autocortes-storage")

# ==================== CLIENTE S3 ====================

def get_s3_client():
    """
    Retorna cliente boto3 configurado para Backblaze B2
    """
    try:
        client = boto3.client(
            "s3",
            endpoint_url=B2_ENDPOINT,
            aws_access_key_id=B2_KEY_ID,
            aws_secret_access_key=B2_APP_KEY,
            config=Config(signature_version="s3v4")
        )
        logger.info("✅ Cliente B2 (S3) inicializado")
        return client
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar cliente B2: {e}")
        return None

# ==================== UPLOAD ====================

def upload_file(file_path: str, remote_path: str) -> Optional[str]:
    """
    Faz upload de arquivo para B2
    
    Args:
        file_path: Caminho local do arquivo
        remote_path: Caminho remoto no bucket (ex: "storyforge/video.mp4")
    
    Returns:
        remote_path se sucesso, None se falhar
    """
    try:
        client = get_s3_client()
        if not client:
            return None
        
        logger.info(f"📤 Uploading para B2: {remote_path}")
        
        with open(file_path, 'rb') as f:
            client.upload_fileobj(f, B2_BUCKET, remote_path)
        
        logger.info(f"✅ Upload concluído: {remote_path}")
        return remote_path
        
    except Exception as e:
        logger.error(f"❌ Falha no upload para B2: {e}")
        return None

# ==================== DOWNLOAD ====================

def download_file(remote_path: str, local_path: str) -> Optional[str]:
    """
    Baixa arquivo do B2
    
    Args:
        remote_path: Caminho remoto no bucket
        local_path: Caminho local para salvar
    
    Returns:
        local_path se sucesso, None se falhar
    """
    try:
        client = get_s3_client()
        if not client:
            return None
        
        logger.info(f"📥 Downloading do B2: {remote_path}")
        
        with open(local_path, 'wb') as f:
            client.download_fileobj(B2_BUCKET, remote_path, f)
        
        logger.info(f"✅ Download concluído: {local_path}")
        return local_path
        
    except Exception as e:
        logger.error(f"❌ Falha no download do B2: {e}")
        return None

# ==================== SIGNED URLS ====================

def generate_signed_download_url(remote_path: str, expires_in: int = 604800) -> Optional[str]:
    """
    Gera URL assinada para download temporário
    
    Args:
        remote_path: Caminho do arquivo no bucket
        expires_in: Tempo de validade em segundos (padrão: 7 dias)
    
    Returns:
        URL assinada se sucesso, None se falhar
    """
    try:
        client = get_s3_client()
        if not client:
            return None
        
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': B2_BUCKET, 'Key': remote_path},
            ExpiresIn=expires_in
        )
        
        logger.info(f"✅ Signed URL gerada (válida por {expires_in}s)")
        return url
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar Signed URL: {e}")
        return None

def generate_signed_upload_url(remote_path: str, expires_in: int = 3600) -> Optional[str]:
    """
    Gera URL assinada para upload temporário
    
    Args:
        remote_path: Caminho do arquivo no bucket
        expires_in: Tempo de validade em segundos (padrão: 1 hora)
    
    Returns:
        URL assinada se sucesso, None se falhar
    """
    try:
        client = get_s3_client()
        if not client:
            return None
        
        url = client.generate_presigned_url(
            'put_object',
            Params={'Bucket': B2_BUCKET, 'Key': remote_path},
            ExpiresIn=expires_in
        )
        
        logger.info(f"✅ Upload Signed URL gerada (válida por {expires_in}s)")
        return url
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar Upload Signed URL: {e}")
        return None

# ==================== LISTAGEM ====================

def list_files(prefix: str = "") -> list:
    """
    Lista arquivos no bucket
    
    Args:
        prefix: Prefixo para filtrar (ex: "storyforge/")
    
    Returns:
        Lista de nomes de arquivos
    """
    try:
        client = get_s3_client()
        if not client:
            return []
        
        response = client.list_objects_v2(
            Bucket=B2_BUCKET,
            Prefix=prefix
        )
        
        files = [obj['Key'] for obj in response.get('Contents', [])]
        logger.info(f"✅ {len(files)} arquivos encontrados")
        return files
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar arquivos: {e}")
        return []

# ==================== DELETAR ====================

def delete_file(remote_path: str) -> bool:
    """
    Deleta arquivo do B2
    
    Args:
        remote_path: Caminho do arquivo no bucket
    
    Returns:
        True se sucesso, False se falhar
    """
    try:
        client = get_s3_client()
        if not client:
            return False
        
        client.delete_object(Bucket=B2_BUCKET, Key=remote_path)
        logger.info(f"✅ Arquivo deletado: {remote_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar arquivo: {e}")
        return False
