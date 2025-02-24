import tempfile
from pathlib import Path
from typing import List, Tuple

import docker
from minio import Minio
from prefect import flow, get_run_logger, task
from prefect.infrastructure import DockerContainer

# Configure docker client from env
docker_client = docker.from_env()


def get_docker_container(image_name: str, volumes: list) -> DockerContainer:
    """
    Create a container configured with a local docker client.
    """
    return DockerContainer(
        image=image_name,
        auto_remove=True,
        stream_output=True,
        volumes=volumes,
        docker_client=docker_client,
        docker_server_url="unix://var/run/docker.sock",
    )


def get_minio_client(
    server: str,
    access_key: str,
    secret_key: str,
) -> Minio:
    """Configure a MinIO client."""
    return Minio(
        server,
        access_key=access_key,
        secret_key=secret_key,
        secure=False,
    )


@task(name="List encrypted files", log_prints=True, tags="SMIDT")
def list_encrypted_files(
    minio_server: str,
    minio_access_key: str,
    minio_secret_key: str,
    bucket_name: str,
    prefix: str = "",
) -> List[str]:
    """List all encrypted files from the input bucket."""
    logger = get_run_logger()
    client = get_minio_client(
        server=minio_server, access_key=minio_access_key, secret_key=minio_secret_key
    )
    encrypted_files = []

    try:
        objects = client.list_objects(bucket_name, prefix=prefix, recursive=True)
        encrypted_files = [
            obj.object_name for obj in objects if obj.object_name.endswith(".p7m.enc")
        ]
        logger.debug(f"Encrypted files list: {encrypted_files}")
    except Exception as e:
        raise Exception(f"Error while listing files from bucket: {e}")

    return encrypted_files


@task(name="Download files from MinIO", log_prints=True, tags="SMIDT")
def download_files_from_minio(
    minio_server: str,
    minio_access_key: str,
    minio_secret_key: str,
    bucket_name: str,
    p12_key: str,
    enc_file_key: str,
    ca_cert_key: str,
) -> Tuple[Path, Path, Path, Path]:
    """Download the P12 certificate and encoded file from MinIO."""
    logger = get_run_logger()
    client = get_minio_client(
        server=minio_server, access_key=minio_access_key, secret_key=minio_secret_key
    )
    temp_dir = Path(tempfile.mkdtemp())

    p12_path = temp_dir / p12_key.partition("/")[-1]
    enc_path = temp_dir / Path(enc_file_key).name
    ca_cert_path = temp_dir / ca_cert_key.partition("/")[-1]

    try:
        client.fget_object(bucket_name, p12_key, str(p12_path))
        logger.debug(f"Downloaded P12 file: {p12_path}")
        client.fget_object(bucket_name, enc_file_key, str(enc_path))
        logger.debug(f"Downloaded encrypted file: {enc_path}")
        client.fget_object(bucket_name, ca_cert_key, str(ca_cert_path))
        logger.debug(f"Downloaded CA certificate file: {enc_path}")
        return p12_path, enc_path, ca_cert_path, temp_dir
    except Exception as e:
        temp_dir.rmdir()
        raise Exception(
            f"There's an error while downloading files {p12_key}, {enc_file_key}, {ca_cert_key} from MinIO: {e}"
        )


@task(name="Extract private key", log_prints=True, retries=3)
def extract_private_key(p12_path: Path, p12_password: str) -> Path:
    """Extract private key from file P12"""
    container = get_docker_container(
        image_name="frapsoft/openssl:latest",
        volumes=[f"{p12_path.parent}:/export"],
    )

    key_path = p12_path.parent / "cifra.pem"

    container.command = f"""
        pkcs12 -clcerts -in /export/{p12_path.name} \
        -out /export/cifra.pem -passin pass:{p12_password} -passout pass:{p12_password}
    """

    container.run()
    return key_path


@task(name="Decrypt", log_prints=True, retries=3)
def decrypt_file(enc_file: Path, key_path: Path, key_password: str) -> Path:
    """Decrypt file using OpenSSL S/MIME"""
    container = get_docker_container(
        image_name="frapsoft/openssl:latest",
        volumes=[f"{enc_file.parent}:/export"],
    )

    output_path = enc_file.with_suffix(".zip")

    container.command = f"""
        smime -decrypt \
        -in /export/{enc_file.name} \
        -inform der \
        -binary \
        -out /export/{output_path.name} \
        -recip /export/{key_path.name} \
        -passin pass:{key_password}
    """

    container.run()
    return output_path


@task(name="Verify and extract", retries=3)
def verify_and_extract(zip_path: Path, ca_cert_path: Path) -> Path:
    """Verify S/MIME signature and extract the content."""
    temp_dir = zip_path.parent
    output_zip = temp_dir / zip_path.name.replace(".p7m", "")

    # Create directories for the extraction
    first_extract_dir = temp_dir / "first_extract"
    final_extract_dir = temp_dir / "final_extract"
    first_extract_dir.mkdir(exist_ok=True)
    final_extract_dir.mkdir(exist_ok=True)

    extract_command = f"""
        /bin/ash -c \
        'apk add --no-cache p7zip && \
        cd /export && \
        7z e {zip_path.name} -so > temp_content'
    """

    extract_container = get_docker_container(
        image_name="alpine:latest",
        volumes=[f"{temp_dir}:/export:rw"],
    )

    extract_container.command = extract_command
    extract_container.run()

    verify_command = f"""
        smime -verify \
        -in /export/temp_content \
        -inform der \
        -binary \
        -out /export/{output_zip.name} \
        -CAfile /export/{ca_cert_path.name}
    """

    verify_container = get_docker_container(
        image_name="frapsoft/openssl:latest",
        volumes=[f"{temp_dir}:/export:rw"],
    )

    verify_container.command = verify_command
    verify_container.run()

    unzip_command = f"""
        /bin/ash -c 'apk add --no-cache unzip && \
        cd /export && \
        unzip {output_zip.name} -d first_extract && \
        cd first_extract && \
        unzip *.zip -d ../final_extract'
    """

    # Finally extract the ZIPs
    unzip_container = get_docker_container(
        image_name="alpine:latest",
        volumes=[f"{temp_dir}:/export:rw"],
    )

    unzip_container.command = unzip_command
    unzip_container.run()

    final_extract_command = f"""
        /bin/ash -c 'apk add --no-cache p7zip unzip && \
        cd /export && \
        unzip {output_zip.name} -d first_extract && \
        cd first_extract && \
        unzip *.zip -d ../final_extract'
    """

    # Configure Docker container for unzipping
    final_extract_container = get_docker_container(
        image_name="alpine:latest",
        volumes=[f"{temp_dir}:/export:rw"],
    )

    final_extract_container.command = final_extract_command
    final_extract_container.run()

    return final_extract_dir


@task(name="Upload to MinIO", log_prints=True, tags="SMIDT")
def upload_to_minio(
    minio_server: str,
    minio_access_key: str,
    minio_secret_key: str,
    file_path: Path,
    bucket_name: str,
    object_name: str,
):
    """Load decrypted file to MinIO"""
    logger = get_run_logger()
    client = get_minio_client(
        server=minio_server, access_key=minio_access_key, secret_key=minio_secret_key
    )
    try:
        client.fput_object(bucket_name, object_name, str(file_path))
        logger.debug(f"Uploaded file: {file_path}")
    except Exception as e:
        raise Exception(f"Error while loading file to MinIO: {e}")


@flow(name="Process smidt file flow", log_prints=True, retries=2)
def process_smidt_file_flow(
    minio_server: str,
    minio_access_key: str,
    minio_secret_key: str,
    input_bucket: str,
    p12_key: str,
    enc_file_key: str,
    ca_cert_key: str,
    p12_password: str,
    key_password: str,
    output_bucket: str,
):
    """
    Flow for processing each single file from SMIDT.

    Args:
        input_bucket: Bucket with input files
        p12_key: Path of the P12 file within the bucket
        enc_file_key: Path of the encrypted file within the bucket
        ca_cert_key: Path of the CA certificato within the bucket
        p12_password: Password of the P12 file
        key_password: Password of the private key
        output_bucket: Output bucket to save decrypted files
    """
    logger = get_run_logger()
    # Download files
    p12_path, enc_path, ca_cert_path, temp_dir = download_files_from_minio(
        minio_server,
        minio_access_key,
        minio_secret_key,
        input_bucket,
        p12_key,
        enc_file_key,
        ca_cert_key,
    )
    try:
        key_path = extract_private_key(p12_path, p12_password)
        logger.info(f"Extract private key {key_path}")

        decrypted_path = decrypt_file(enc_path, key_path, key_password)
        logger.info(f"Decrypted path file {decrypted_path}")

        final_dir = verify_and_extract(decrypted_path, ca_cert_path)
        logger.info(f"Final directory {final_dir}")

        # Upload all extracted files
        for file_path in final_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(final_dir)
                upload_to_minio(
                    minio_server,
                    minio_access_key,
                    minio_secret_key,
                    file_path,
                    output_bucket,
                    str(relative_path),
                )

    finally:
        # Clean temporary directories
        for item in temp_dir.rglob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
        temp_dir.rmdir()
