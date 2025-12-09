"""
🔒 B2 Storage Module - Integração Backblaze B2 (Secure Signed URLs)
Gerencia uploads, downloads e URLs temporárias privadas usando b2sdk.v2.
"""

import os
import logging
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# Configuração de Logs
logger = logging.getLogger("B2Storage")

def get_b2_api():
    """
    Inicializa e autentica o cliente B2Api usando variáveis de ambiente.
    Retorna a instância autenticada da API e o objeto bucket.
    """
    try:
        key_id = os.getenv("B2_KEY_ID")
        application_key = os.getenv("B2_APPLICATION_KEY")
        bucket_name = os.getenv("B2_BUCKET_NAME")

        if not all([key_id, application_key, bucket_name]):
            # Em ambiente de teste local pode não estar setado, mas no RunPod é crítico
            logger.warning("Variáveis B2 não encontradas. Upload será pulado.")
            return None, None

        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", key_id, application_key)
        
        bucket = b2_api.get_bucket_by_name(bucket_name)
        return b2_api, bucket

    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao Backblaze B2: {e}")
        return None, None

def upload_file(file_path: str, file_name: str) -> str:
    """
    Faz upload de um arquivo local para o bucket privado.
    Sobrescreve se já existir. Retorna o nome do arquivo no bucket.
    """
    try:
        _, bucket = get_b2_api()
        if not bucket: return None
        
        logger.info(f"📤 Iniciando upload para B2: {file_name}")
        
        bucket.upload_local_file(
            local_file=file_path,
            file_name=file_name
        )
        
        logger.info(f"✅ Upload concluído: {file_name}")
        return file_name

    except Exception as e:
        logger.error(f"❌ Falha no upload para B2: {e}")
        return None # Retorna None para o handler saber que falhou, mas não crashar o job todo

def generate_signed_download_url(file_name: str, expires_in: int = 3600) -> str:
    """
    Gera uma URL assinada (privada) para download temporário.
    """
    try:
        _, bucket = get_b2_api()
        if not bucket: return None
        
        auth_token = bucket.get_download_authorization(
            file_name_prefix=file_name,
            valid_duration_in_seconds=expires_in
        )
        
        download_url_base = bucket.get_download_url(file_name)
        signed_url = f"{download_url_base}?Authorization={auth_token}"
        
        return signed_url

    except Exception as e:
        logger.error(f"❌ Erro ao gerar Signed URL B2: {e}")
        return None
