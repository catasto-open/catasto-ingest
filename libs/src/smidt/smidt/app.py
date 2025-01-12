# Example usage

from smidt.client import FTPConfig
from smidt.config import settings
from smidt.watcher import FTPMinioObserver

if __name__ == "__main__":
    ftp_config = FTPConfig(
        host=settings.FTP_HOST, user=settings.FTP_USER, password=settings.FTP_PASSWORD
    )

    observer = FTPMinioObserver(
        # Filesystem configuration
        ftp_config=ftp_config,
        remote_dir=settings.FTP_BASEPATH,
        lock_filename=settings.FTP_EVENT_FILENAME,
        # MinIO configuration
        minio_endpoint=settings.MINIO_HOST,
        minio_access_key=settings.MINIO_ACCESS_KEY,
        minio_secret_key=settings.MINIO_SECRET_KEY,
        minio_bucket=settings.MINIO_BUCKET,
        minio_secure=False,
    )
    # Start monitoring
    for transferred_files in observer.start_monitoring(interval=600):
        for transfer in transferred_files:
            print(f"File: {transfer.filename}")
            print(f"Size: {transfer.size or 'unknown'} bytes")
            print(f"Path: {transfer.bucket}/{transfer.minio_path}")
            print(f"Timestamp: {transfer.timestamp.isoformat()}")
