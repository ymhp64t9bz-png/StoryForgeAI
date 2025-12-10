"""
🔒 B2 Storage Module - Backblaze B2 (Signed URL Support)
"""

import os
import logging
from b2sdk.v2 import InMemoryAccountInfo, B2Api

logger = logging.getLogger("B2Storage")

def get_b2_api():
    try:
        key_id = os.getenv("B2_KEY_ID")
        application_key = os.getenv("B2_APPLICATION_KEY")
        bucket_name = os.getenv("B2_BUCKET_NAME")

        if not all([key_id, application_key, bucket_name]):
            raise ValueError("❌ Variáveis B2 não configuradas corretamente.")

        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", key_id, application_key)

        bucket = b2_api.get_bucket_by_name(bucket_name)
        return b2_api, bucket

    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao B2: {e}")
        raise e


def upload_file(file_path: str, file_name: str):
    try:
        _, bucket = get_b2_api()

        logger.info(f"📤 Upload B2: {file_name}")

        bucket.upload_local_file(
            local_file=file_path,
            file_name=file_name
        )
        return file_name

    except Exception as e:
        logger.error(f"❌ Falha Upload: {e}")
        raise e


def generate_signed_download_url(file_name: str, expires_in: int = 3600) -> str:
    try:
        _, bucket = get_b2_api()

        auth_token = bucket.get_download_authorization(
            file_name_prefix=file_name,
            valid_duration_in_seconds=expires_in
        )

        base_url = bucket.get_download_url(file_name)

        return f"{base_url}?Authorization={auth_token}"

    except Exception as e:
        logger.error(f"❌ Erro Signed URL: {e}")
        return None

