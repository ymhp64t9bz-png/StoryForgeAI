import os
import logging
from b2sdk.v2 import InMemoryAccountInfo, B2Api

logger = logging.getLogger("B2Storage")


def get_b2_client():
    key_id = os.getenv("B2_KEY_ID")
    application_key = os.getenv("B2_APPLICATION_KEY")
    bucket_name = os.getenv("B2_BUCKET_NAME")

    if not all([key_id, application_key, bucket_name]):
        raise ValueError("Missing Backblaze credentials.")

    info = InMemoryAccountInfo()
    b2 = B2Api(info)
    b2.authorize_account("production", key_id, application_key)

    bucket = b2.get_bucket_by_name(bucket_name)
    return b2, bucket


def upload_file(path, name):
    _, bucket = get_b2_client()
    bucket.upload_local_file(local_file=path, file_name=name)
    return True


def generate_signed_download_url(name, expires=3600):
    b2, bucket = get_b2_client()

    auth = bucket.get_download_authorization(
        file_name_prefix=name,
        valid_duration_in_seconds=expires
    )

    base = b2.get_download_url_for_file_name(bucket.name, name)
    return f"{base}?Authorization={auth}"


def delete_file(name):
    _, bucket = get_b2_client()

    for file_version, _ in bucket.ls(name):
        bucket.delete_file_version(file_version.id_, name)
        return True
    return False
