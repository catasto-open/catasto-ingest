from pathlib import Path

from prefect import flow, get_run_logger, task
from prefect.blocks.system import JSON
from smidt.client import FTPConfig
from smidt.models import TransferredFile
from smidt.watcher import FTPMinioObserver

from flows.smidt_decrypt import process_smidt_file_flow

smidt_block = JSON.load("smidt-settings")


@task(name="copy monthly files", log_prints=True, tags="SMIDT")
def observe_and_copy():
    ftp_config = FTPConfig(
        host=smidt_block.value["ftp_host"],
        user=smidt_block.value["ftp_user"],
        password=smidt_block.value["ftp_password"],
    )

    observer = FTPMinioObserver(
        # Filesystem configuration
        ftp_config=ftp_config,
        remote_dir=smidt_block.value["ftp_basepath"],
        lock_filename=smidt_block.value["ftp_event_filename"],
        # MinIO configuration
        minio_endpoint=smidt_block.value["minio_host"],
        minio_access_key=smidt_block.value["minio_access_key"],
        minio_secret_key=smidt_block.value["minio_secret_key"],
        minio_bucket=smidt_block.value["minio_bucket"],
        minio_secure=False,
    )
    # transfer new files
    for transferred_files in observer.start_monitoring(single_run=True):
        return transferred_files


@task(name="copy monthly files", log_prints=True, tags="SMIDT")
def get_file_from_bucket(filename: str, bucket: str):
    tmp_path = Path("/tmp")


@flow(name="smidt decode and extract", log_prints=True)
def smidt_extract_flow(file: TransferredFile):
    logger = get_run_logger()
    logger.info("Running smidt extract file flow")
    downloaded = get_file_from_bucket(filename=file.filename, bucket=file.bucket)
    return None


@flow(name="smidt flow", log_prints=True)
def smidt_flow():
    logger = get_run_logger()
    logger.info("Running smidt flow")
    files = observe_and_copy()
    logger.info(f"Files found in the smidt server: {files}")
    if files:
        for file in files:
            process_smidt_file_flow(
                minio_server=smidt_block.value["minio_host"],
                minio_access_key=smidt_block.value["minio_access_key"],
                minio_secret_key=smidt_block.value["minio_secret_key"],
                input_bucket=smidt_block.value["minio_bucket"],
                p12_key=smidt_block.value["p12_certificate"],
                enc_file_key=file.filename,
                ca_cert_key=smidt_block.value["CA_certificate"],
                p12_password=smidt_block.value["p12_password"],
                key_password=smidt_block.value["key_password"],
                output_bucket=smidt_block.value["siscat_bucket"],
            )
    else:
        logger.info("There isn't any new file to process!")


if __name__ == "__main__":
    smidt_flow()
