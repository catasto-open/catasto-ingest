from prefect import flow, get_run_logger, task
from prefect.blocks.system import JSON
from smidt.client import FTPConfig
from smidt.watcher import FTPMinioObserver

from flows.duckdb_loader import ct2duckdb_flow
from flows.smidt_decrypt import process_smidt_file_flow
from flows.smidt_loader import ctcn_sync_flow, ctmp_sync_flow
from flows.smidt_prepare import download_and_sort_flow

smidt_block = JSON.load("smidt-settings")
catastodb_block = JSON.load("catasto-settings")


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


@flow(name="smidt flow", log_prints=True)
def smidt_flow():
    logger = get_run_logger()
    logger.info("Running smidt flow")
    files = observe_and_copy()
    logger.info(f"Files found in the smidt server: {files}")
    if files:
        cadaster_files = []
        for file in files:
            cadaster_files += process_smidt_file_flow(
                minio_server=smidt_block.value["minio_host"],
                minio_access_key=smidt_block.value["minio_access_key"],
                minio_secret_key=smidt_block.value["minio_secret_key"],
                input_bucket=smidt_block.value["minio_bucket"],
                p12_key=smidt_block.value["p12_certificate"],
                enc_file_key=file.filename,
                ca_cert_key=smidt_block.value["CA_certificate"],
                p12_password=smidt_block.value["p12_password"],
                key_password=smidt_block.value["key_password"],
                output_bucket=smidt_block.value["catasto_bucket"],
            )
        return cadaster_files
    else:
        logger.info("There isn't any new file to process!")


if __name__ == "__main__":
    files = smidt_flow()
    local_sorted_files = download_and_sort_flow(
        files_list=files,
        minio_endpoint=smidt_block.value["minio_host"],
        minio_access_key=smidt_block.value["minio_access_key"],
        minio_secret_key=smidt_block.value["minio_secret_key"],
        minio_bucket=smidt_block.value["catasto_bucket"],
        secure=False,
    )
    ddb_file = ct2duckdb_flow(
        fab_files=local_sorted_files["FAB"],
        ter_files=local_sorted_files["TER"],
        sog_files=local_sorted_files["SOG"],
        tit_files=local_sorted_files["TIT"],
        cxf_files=local_sorted_files["CXF"],
        catasto_db=catastodb_block.value["duckdb_conn_string"],
        empty_db=True,
    )
    ctcn_sync_flow(
        source_db=ddb_file,
        target_db=catastodb_block.value["pg_conn_string"],
    )
    ctmp_sync_flow(
        source_db=ddb_file,
        target_db=catastodb_block.value["pg_conn_string"],
    )
