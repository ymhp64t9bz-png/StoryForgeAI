"""
🔒 Secure Storage Service - StoryForge AI
Gerencia uploads, downloads e URLs assinadas (Signed URLs) para AWS S3, R2, GCS ou MinIO.
Garante que nenhum arquivo seja público. RunPod acessa via URLs temporárias seguras.
"""

import boto3
import os
import logging
import uuid
from botocore.exceptions import NoCredentialsError, ClientError

logger = logging.getLogger(__name__)

class SecureStorageService:
    def __init__(self):
        # Carrega credenciais do ambiente (Suporta AWS, R2, MinIO, GCS Interop)
        self.bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME", "storyforge-private")
        self.region = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"), # Opcional: Para R2/MinIO
                region_name=self.region
            )
            logger.info(f"✅ Secure Storage conectado ao bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"⚠️ Secure Storage falhou ao iniciar (Verifique .env): {e}")
            self.s3_client = None

    def generate_upload_signed_url(self, filename: str, content_type: str = "video/mp4", expiration=3600):
        """
        Gera uma URL assinada (PUT) para o Frontend ou Cliente fazer upload direto.
        O arquivo vai para uma pasta privada /uploads.
        """
        if not self.s3_client: return None

        object_name = f"private/uploads/{uuid.uuid4()}_{filename}"
        
        try:
            response = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name,
                    'ContentType': content_type
                },
                ExpiresIn=expiration
            )
            return {"upload_url": response, "key": object_name}
        except ClientError as e:
            logger.error(f"❌ Erro ao gerar Upload URL: {e}")
            return None

    def generate_download_signed_url(self, object_key: str, expiration=3600):
        """
        Gera uma URL assinada (GET) para visualização ou download seguro.
        A URL expira em 'expiration' segundos.
        """
        if not self.s3_client: return None

        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"❌ Erro ao gerar Download URL: {e}")
            return None

    def upload_file_from_local(self, local_path: str, target_folder="private/outputs"):
        """
        Faz upload de um arquivo local para o bucket privado.
        Usado pelo Handler para salvar o vídeo final.
        """
        if not self.s3_client: return None

        filename = os.path.basename(local_path)
        object_name = f"{target_folder}/{uuid.uuid4()}_{filename}"

        try:
            self.s3_client.upload_file(local_path, self.bucket_name, object_name)
            logger.info(f"📤 Upload concluído: {object_name}")
            return object_name # Retorna a CHAVE, não a URL (URL deve ser gerada sob demanda)
        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: {local_path}")
            return None
        except NoCredentialsError:
            logger.error("❌ Credenciais AWS não encontradas")
            return None

    def download_file_to_local(self, object_key: str, local_path: str):
        """Baixa arquivo do bucket para processamento local"""
        if not self.s3_client: return False
        
        try:
            self.s3_client.download_file(self.bucket_name, object_key, local_path)
            return True
        except ClientError as e:
            logger.error(f"❌ Erro no download: {e}")
            return False

# Singleton
storage = SecureStorageService()
