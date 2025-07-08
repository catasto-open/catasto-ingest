import io
import tarfile
import tempfile
import uuid
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
        logger.error(
            f"Error while downloading files {p12_key}, {enc_file_key}, {ca_cert_key} from MinIO"
        )
        raise Exception(
            f"There's an error while downloading files {p12_key}, {enc_file_key}, {ca_cert_key} from MinIO: {e}"
        )


@task(name="Extract private key", log_prints=True, retries=3)
def extract_private_key(p12_path: Path, p12_password: str, dind: bool = False) -> Path:
    """Extract private key from file P12

    Args:
        p12_path: Path to the P12 file
        p12_password: Password for the P12 file
        dind: Use Docker volume approach for Docker-in-Docker (default: False)

    Returns:
        Path to the extracted private key file
    """

    key_path = p12_path.parent / "cifra.pem"

    if dind:
        print("Using Docker volume approach for Docker-in-Docker")
        return _extract_private_key_docker_volume(p12_path, p12_password, key_path)
    else:
        print("Using standard Docker container approach")
        return _extract_private_key_standard(p12_path, p12_password, key_path)


def _extract_private_key_standard(
    p12_path: Path, p12_password: str, key_path: Path
) -> Path:
    """Standard extraction using direct volume mount (original logic)"""

    container = get_docker_container(
        image_name="frapsoft/openssl:latest",
        volumes=[f"{p12_path.parent}:/export"],
    )

    container.command = f"""
        pkcs12 -clcerts -in /export/{p12_path.name} \
        -out /export/cifra.pem \
        -passin pass:{p12_password} \
        -passout pass:{p12_password}
    """

    container.run()

    if not key_path.exists():
        raise Exception("Error while extracting private key from P12 file")

    return key_path


def _extract_private_key_docker_volume(
    p12_path: Path, p12_password: str, key_path: Path
) -> Path:
    """Docker-in-Docker extraction using temporary Docker volume"""

    if not p12_path.exists():
        raise FileNotFoundError(f"P12 file not found: {p12_path}")

    client = docker.from_env()
    volume_name = f"openssl-temp-{uuid.uuid4().hex[:8]}"
    created_containers = []  # Track containers for cleanup
    volume = None

    try:
        # Crea volume temporaneo
        volume = client.volumes.create(name=volume_name)
        print(f"Created temporary volume: {volume_name}")

        # Passo 1: Copia P12 nel volume
        print(f"Copying P12 file {p12_path.name} to volume...")
        with open(p12_path, "rb") as f:
            p12_data = f.read()

        # Crea tar con il file P12
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            info = tarfile.TarInfo(name=p12_path.name)
            info.size = len(p12_data)
            tar.addfile(info, io.BytesIO(p12_data))
        tar_buffer.seek(0)

        # Copia nel volume usando container temporaneo
        copy_container = client.containers.run(
            image="alpine:latest",
            command="sleep 1",
            volumes={volume_name: {"bind": "/shared", "mode": "rw"}},
            detach=True,
            remove=False,
        )
        created_containers.append(copy_container)

        copy_container.put_archive("/shared", tar_buffer.getvalue())
        copy_container.wait()
        print("P12 file copied to volume successfully")

        # Passo 2: Esegui OpenSSL (questo container si auto-rimuove)
        print("Running OpenSSL extraction...")
        try:
            openssl_result = client.containers.run(
                image="frapsoft/openssl:latest",
                command=f"pkcs12 -clcerts -in /shared/{p12_path.name} -out /shared/cifra.pem -passin pass:{p12_password} -passout pass:{p12_password}",
                volumes={volume_name: {"bind": "/shared", "mode": "rw"}},
                remove=True,  # Auto-remove dopo execution
            )
            print("OpenSSL container executed successfully")
        except Exception as openssl_error:
            print(f"OpenSSL execution failed: {openssl_error}")
            raise Exception(f"OpenSSL extraction failed: {openssl_error}")

        # Passo 3: Recupera il file risultante
        print("Extracting private key from volume...")
        extract_container = client.containers.run(
            image="alpine:latest",
            command="sleep 1",
            volumes={volume_name: {"bind": "/shared", "mode": "ro"}},
            detach=True,
            remove=False,
        )
        created_containers.append(extract_container)

        # Estrai il file cifra.pem
        try:
            archive_stream, _ = extract_container.get_archive("/shared/cifra.pem")

            # Estrai dal tar
            tar_data = b"".join(archive_stream)
            tar_buffer = io.BytesIO(tar_data)

            with tarfile.open(fileobj=tar_buffer) as tar:
                pem_file = tar.extractfile("cifra.pem")
                if pem_file:
                    with open(key_path, "wb") as f:
                        f.write(pem_file.read())
                    print(f"Private key extracted to: {key_path}")
                else:
                    raise Exception("Could not extract cifra.pem from archive")

        except docker.errors.NotFound:
            raise Exception("cifra.pem not found in volume - OpenSSL extraction failed")

        if not key_path.exists():
            raise Exception("Error while extracting private key from P12 file")

        return key_path

    except Exception as e:
        print(f"Error during Docker volume extraction: {e}")
        raise Exception("Error while extracting private key from P12 file")
    finally:
        # Cleanup containers prima del volume
        for container in created_containers:
            try:
                # Ferma il container se è ancora in running
                if container.status == "running":
                    print(f"Stopping container {container.short_id}...")
                    container.stop(timeout=5)

                # Rimuovi il container
                container.remove(force=True)
                print(f"Removed container {container.short_id}")
            except Exception as container_error:
                print(
                    f"Warning: Could not cleanup container {container.short_id}: {container_error}"
                )
                # Prova rimozione forzata
                try:
                    container.remove(force=True)
                except:
                    pass

        # Cleanup volume dopo aver rimosso tutti i container
        if volume:
            try:
                # Aspetta un momento per essere sicuri che i container siano liberati
                import time

                time.sleep(1)

                volume.remove(force=True)
                print(f"Cleaned up volume: {volume_name}")
            except Exception as cleanup_error:
                print(
                    f"Warning: Could not cleanup volume {volume_name}: {cleanup_error}"
                )
                # Prova a forzare la rimozione del volume
                try:
                    client.api.remove_volume(volume_name, force=True)
                    print(f"Force removed volume: {volume_name}")
                except:
                    print(f"Volume {volume_name} may need manual cleanup")


@task(name="Decrypt", log_prints=True, retries=3)
def decrypt_file(
    enc_file: Path, key_path: Path, key_password: str, dind: bool = False
) -> Path:
    """Decrypt file using OpenSSL S/MIME

    Args:
        enc_file: Path to the encrypted file
        key_path: Path to the private key file
        key_password: Password for the private key
        dind: Use Docker volume approach for Docker-in-Docker (default: False)

    Returns:
        Path to the decrypted file
    """

    output_path = enc_file.with_suffix(".zip")

    if dind:
        print("Using Docker volume approach for decryption")
        return _decrypt_file_docker_volume(
            enc_file, key_path, key_password, output_path
        )
    else:
        print("Using standard Docker container approach for decryption")
        return _decrypt_file_standard(enc_file, key_path, key_password, output_path)


def _decrypt_file_standard(
    enc_file: Path, key_path: Path, key_password: str, output_path: Path
) -> Path:
    """Standard decryption using direct volume mount (original logic)"""

    container = get_docker_container(
        image_name="frapsoft/openssl:latest",
        volumes=[f"{enc_file.parent}:/export"],
    )

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


def _decrypt_file_docker_volume(
    enc_file: Path, key_path: Path, key_password: str, output_path: Path
) -> Path:
    """Docker-in-Docker decryption using temporary Docker volume"""

    if not enc_file.exists():
        raise FileNotFoundError(f"Encrypted file not found: {enc_file}")
    if not key_path.exists():
        raise FileNotFoundError(f"Key file not found: {key_path}")

    client = docker.from_env()
    volume_name = f"decrypt-temp-{uuid.uuid4().hex[:8]}"
    created_containers = []
    volume = None

    try:
        # Crea volume temporaneo
        volume = client.volumes.create(name=volume_name)
        print(f"Created temporary volume: {volume_name}")

        # Passo 1: Copia entrambi i file nel volume
        print(f"Copying files to volume: {enc_file.name} and {key_path.name}")

        # Leggi entrambi i file
        with open(enc_file, "rb") as f:
            enc_data = f.read()
        with open(key_path, "rb") as f:
            key_data = f.read()

        # Crea tar con entrambi i file
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            # Aggiungi file crittografato
            enc_info = tarfile.TarInfo(name=enc_file.name)
            enc_info.size = len(enc_data)
            tar.addfile(enc_info, io.BytesIO(enc_data))

            # Aggiungi file chiave
            key_info = tarfile.TarInfo(name=key_path.name)
            key_info.size = len(key_data)
            tar.addfile(key_info, io.BytesIO(key_data))
        tar_buffer.seek(0)

        # Copia nel volume usando container temporaneo
        copy_container = client.containers.run(
            image="alpine:latest",
            command="sleep 1",
            volumes={volume_name: {"bind": "/shared", "mode": "rw"}},
            detach=True,
            remove=False,
        )
        created_containers.append(copy_container)

        copy_container.put_archive("/shared", tar_buffer.getvalue())
        copy_container.wait()
        print("Files copied to volume successfully")

        # Passo 2: Esegui OpenSSL smime decrypt
        print("Running OpenSSL S/MIME decryption...")
        try:
            decrypt_result = client.containers.run(
                image="frapsoft/openssl:latest",
                command=f"""smime -decrypt -in /shared/{enc_file.name} -inform der -binary -out /shared/{output_path.name} -recip /shared/{key_path.name} -passin pass:{key_password}""",
                volumes={volume_name: {"bind": "/shared", "mode": "rw"}},
                remove=True,
            )
            print("OpenSSL S/MIME decryption executed successfully")
        except Exception as decrypt_error:
            print(f"Decryption failed: {decrypt_error}")
            raise Exception(f"OpenSSL S/MIME decryption failed: {decrypt_error}")

        # Passo 3: Recupera il file decrittografato
        print("Extracting decrypted file from volume...")
        extract_container = client.containers.run(
            image="alpine:latest",
            command="sleep 1",
            volumes={volume_name: {"bind": "/shared", "mode": "ro"}},
            detach=True,
            remove=False,
        )
        created_containers.append(extract_container)

        # Estrai il file decrittografato
        try:
            archive_stream, _ = extract_container.get_archive(
                f"/shared/{output_path.name}"
            )

            # Estrai dal tar
            tar_data = b"".join(archive_stream)
            tar_buffer = io.BytesIO(tar_data)

            with tarfile.open(fileobj=tar_buffer) as tar:
                decrypted_file = tar.extractfile(output_path.name)
                if decrypted_file:
                    with open(output_path, "wb") as f:
                        f.write(decrypted_file.read())
                    print(f"Decrypted file extracted to: {output_path}")
                else:
                    raise Exception(
                        f"Could not extract {output_path.name} from archive"
                    )

        except docker.errors.NotFound:
            raise Exception(
                f"{output_path.name} not found in volume - decryption failed"
            )

        if not output_path.exists():
            raise Exception("Error while decrypting file")

        return output_path

    except Exception as e:
        print(f"Error during Docker volume decryption: {e}")
        raise Exception("Error while decrypting file")
    finally:
        # Cleanup containers prima del volume
        for container in created_containers:
            try:
                if container.status == "running":
                    print(f"Stopping container {container.short_id}...")
                    container.stop(timeout=5)

                container.remove(force=True)
                print(f"Removed container {container.short_id}")
            except Exception as container_error:
                print(
                    f"Warning: Could not cleanup container {container.short_id}: {container_error}"
                )
                try:
                    container.remove(force=True)
                except:
                    pass

        # Cleanup volume
        if volume:
            try:
                import time

                time.sleep(1)

                volume.remove(force=True)
                print(f"Cleaned up volume: {volume_name}")
            except Exception as cleanup_error:
                print(
                    f"Warning: Could not cleanup volume {volume_name}: {cleanup_error}"
                )
                try:
                    client.api.remove_volume(volume_name, force=True)
                    print(f"Force removed volume: {volume_name}")
                except:
                    print(f"Volume {volume_name} may need manual cleanup")


@task(name="Verify and extract", retries=3)
def verify_and_extract(
    zip_path: Path, ca_cert_path: Path, dind: bool = False
) -> Tuple[Path, str]:
    """Verify S/MIME signature and extract the content.

    Args:
        zip_path: Path to the ZIP file
        ca_cert_path: Path to the CA certificate file
        dind: Use Docker volume approach for Docker-in-Docker (default: False)

    Returns:
        Tuple of (final_extract_dir, folder_name)
    """

    logger = get_run_logger()

    if dind:
        print("Using Docker volume approach for verify and extract")
        return _verify_and_extract_docker_volume(zip_path, ca_cert_path, logger)
    else:
        print("Using standard Docker container approach for verify and extract")
        return _verify_and_extract_standard(zip_path, ca_cert_path, logger)


def _verify_and_extract_standard(
    zip_path: Path, ca_cert_path: Path, logger
) -> Tuple[Path, str]:
    """Versione originale con comandi Alpine migliorati"""

    logger = get_run_logger()
    temp_dir = zip_path.parent
    output_zip = temp_dir / zip_path.name.replace(".p7m", "")

    # Create directories for the extraction
    first_extract_dir = temp_dir / "first_extract"
    final_extract_dir = temp_dir / "final_extract"
    first_extract_dir.mkdir(exist_ok=True)
    final_extract_dir.mkdir(exist_ok=True)

    # MIGLIORATO: Comando 7z senza update (immagine con p7zip preinstallato o base)
    extract_command = f"""
        /bin/ash -c \
        '(apk add --no-cache p7zip 2>/dev/null || apk add --no-cache p7zip-full 2>/dev/null || echo "Using pre-installed tools") && \
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

    # Extract first ZIP and get the name of the inner ZIP file
    # MIGLIORATO: Comando unzip senza update
    unzip_command = f"""
        /bin/ash -c '(apk add --no-cache unzip 2>/dev/null || echo "Using pre-installed unzip") && \
        cd /export && \
        unzip {output_zip.name} -d first_extract && \
        ls /export/first_extract/*.zip > /export/inner_zip_name.txt'
    """
    unzip_container = get_docker_container(
        image_name="alpine:latest",
        volumes=[f"{temp_dir}:/export:rw"],
    )
    unzip_container.command = unzip_command
    unzip_container.run()

    # Read the inner ZIP filename
    inner_zip_path = temp_dir / "inner_zip_name.txt"
    inner_zip_name = ""
    if inner_zip_path.exists():
        inner_zip_name = inner_zip_path.read_text().strip()
        inner_zip_name = Path(inner_zip_name).name
        logger.info(f"Inner ZIP file name: {inner_zip_name}")

    # Create a directory with the inner ZIP name (without .zip extension)
    folder_name = Path(inner_zip_name).stem if inner_zip_name else "extracted"
    final_extract_dir = temp_dir / folder_name
    final_extract_dir.mkdir(exist_ok=True)

    # Extract the second ZIP to the named directory
    # MIGLIORATO: Comando unzip finale senza update
    final_extract_command = f"""
        /bin/ash -c '(apk add --no-cache unzip 2>/dev/null || echo "Using pre-installed unzip") && \
        cd /export/first_extract && \
        unzip *.zip -d /export/{folder_name}'
    """
    final_extract_container = get_docker_container(
        image_name="alpine:latest",
        volumes=[f"{temp_dir}:/export:rw"],
    )
    final_extract_container.command = final_extract_command
    final_extract_container.run()

    return final_extract_dir, folder_name


def _verify_and_extract_docker_volume(
    zip_path: Path, ca_cert_path: Path, logger
) -> Tuple[Path, str]:
    """Versione Docker volume senza apk update - solo tool preinstallati"""

    temp_dir = zip_path.parent
    output_zip_name = zip_path.name.replace(".p7m", "")

    client = docker.from_env()
    volume_name = f"verify-temp-{uuid.uuid4().hex[:8]}"
    created_containers = []
    volume = None

    try:
        # Crea volume temporaneo
        volume = client.volumes.create(name=volume_name)
        print(f"Created temporary volume: {volume_name}")

        # Copia file nel volume
        with open(zip_path, "rb") as f:
            zip_data = f.read()
        with open(ca_cert_path, "rb") as f:
            ca_cert_data = f.read()

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            zip_info = tarfile.TarInfo(name=zip_path.name)
            zip_info.size = len(zip_data)
            tar.addfile(zip_info, io.BytesIO(zip_data))

            ca_info = tarfile.TarInfo(name=ca_cert_path.name)
            ca_info.size = len(ca_cert_data)
            tar.addfile(ca_info, io.BytesIO(ca_cert_data))
        tar_buffer.seek(0)

        copy_container = client.containers.run(
            image="alpine:latest",
            command="sleep 1",
            volumes={volume_name: {"bind": "/shared", "mode": "rw"}},
            detach=True,
            remove=False,
        )
        created_containers.append(copy_container)
        copy_container.put_archive("/shared", tar_buffer.getvalue())
        copy_container.wait()

        # Passo 1: Estrazione 7z - solo immagine specializzata
        print("Running 7z extraction with specialized image...")
        client.containers.run(
            image="crazymax/7zip:latest",
            command=f"/bin/sh -c '7z e /shared/{zip_path.name} -so > /shared/temp_content'",
            volumes={volume_name: {"bind": "/shared", "mode": "rw"}},
            remove=True,
        )
        print("7z extraction completed")

        # Passo 2: Verifica S/MIME
        print("Running S/MIME verification...")
        client.containers.run(
            image="frapsoft/openssl:latest",
            command=f"smime -verify -in /shared/temp_content -inform der -binary -out /shared/{output_zip_name} -CAfile /shared/{ca_cert_path.name}",
            volumes={volume_name: {"bind": "/shared", "mode": "rw"}},
            remove=True,
        )
        print("S/MIME verification completed")

        # Passo 3: Prima estrazione ZIP - solo Alpine preinstallato
        print("Running first ZIP extraction with Alpine...")
        client.containers.run(
            image="alpine:latest",
            command=f"""
                /bin/ash -c 'cd /shared && mkdir -p first_extract && 
                unzip {output_zip_name} -d first_extract && 
                ls /shared/first_extract/*.zip > /shared/inner_zip_name.txt'
            """,
            volumes={volume_name: {"bind": "/shared", "mode": "rw"}},
            remove=True,
        )
        print("First ZIP extraction completed")

        # Passo 4: Leggi nome ZIP interno
        read_container = client.containers.run(
            image="alpine:latest",
            command="sleep 1",
            volumes={volume_name: {"bind": "/shared", "mode": "ro"}},
            detach=True,
            remove=False,
        )
        created_containers.append(read_container)

        try:
            archive_stream, _ = read_container.get_archive("/shared/inner_zip_name.txt")
            tar_data = b"".join(archive_stream)
            tar_buffer = io.BytesIO(tar_data)

            with tarfile.open(fileobj=tar_buffer) as tar:
                name_file = tar.extractfile("inner_zip_name.txt")
                if name_file:
                    inner_zip_full_path = name_file.read().decode().strip()
                    inner_zip_name = Path(inner_zip_full_path).name
                    logger.info(f"Inner ZIP file name: {inner_zip_name}")
                else:
                    inner_zip_name = "unknown.zip"
        except:
            inner_zip_name = "unknown.zip"

        folder_name = Path(inner_zip_name).stem if inner_zip_name else "extracted"
        print(f"Final extraction folder: {folder_name}")

        # Passo 5: Estrazione finale - solo Alpine preinstallato
        print("Running final ZIP extraction with Alpine...")
        client.containers.run(
            image="alpine:latest",
            command=f"""
                /bin/ash -c 'cd /shared/first_extract && mkdir -p /shared/{folder_name} && 
                unzip *.zip -d /shared/{folder_name}'
            """,
            volumes={volume_name: {"bind": "/shared", "mode": "rw"}},
            remove=True,
        )
        print("Final ZIP extraction completed")

        # Passo 6: Recupera directory finale
        final_container = client.containers.run(
            image="alpine:latest",
            command="sleep 1",
            volumes={volume_name: {"bind": "/shared", "mode": "ro"}},
            detach=True,
            remove=False,
        )
        created_containers.append(final_container)

        final_extract_dir = temp_dir / folder_name
        final_extract_dir.mkdir(exist_ok=True)

        archive_stream, _ = final_container.get_archive(f"/shared/{folder_name}")
        tar_data = b"".join(archive_stream)
        tar_buffer = io.BytesIO(tar_data)

        with tarfile.open(fileobj=tar_buffer) as tar:
            for member in tar.getmembers():
                if member.isfile():
                    relative_path = Path(member.name).relative_to(folder_name)
                    target_path = final_extract_dir / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    file_obj = tar.extractfile(member)
                    if file_obj:
                        with open(target_path, "wb") as f:
                            f.write(file_obj.read())

        print(f"Extraction completed successfully: {final_extract_dir}")
        return final_extract_dir, folder_name

    except Exception as e:
        print(f"Error: {e}")
        raise Exception("Error while verifying and extracting")
    finally:
        # Cleanup
        for container in created_containers:
            try:
                if container.status == "running":
                    container.stop(timeout=5)
                container.remove(force=True)
            except:
                pass

        if volume:
            try:
                import time

                time.sleep(1)
                volume.remove(force=True)
            except:
                pass


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
        original_path = Path(enc_file_key)
        logger.info(f"Original path {original_path}")
        prefix_path = ""
        if len(original_path.parts) > 2:
            prefix_path = f"{original_path.parts[0]}/{original_path.parts[1]}/"

        key_path = extract_private_key(p12_path, p12_password, dind=True)
        logger.info(f"Extract private key {key_path}")

        decrypted_path = decrypt_file(enc_path, key_path, key_password, dind=True)
        logger.info(f"Decrypted path file {decrypted_path}")

        final_dir, folder_name = verify_and_extract(
            decrypted_path, ca_cert_path, dind=True
        )
        logger.info(f"Final directory {final_dir}, folder name {folder_name}")

        # Upload all extracted files with the correct prefix
        dest_paths = []
        for file_path in final_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(final_dir)
                dest_path = f"{prefix_path}{folder_name}/{relative_path}"
                logger.info(f"Uploading to the destination path {dest_path}")

                upload_to_minio(
                    minio_server,
                    minio_access_key,
                    minio_secret_key,
                    file_path,
                    output_bucket,
                    dest_path,
                )
                dest_paths.append(dest_path)

        return dest_paths

    finally:
        # Clean temporary directories usando pathlib
        try:
            # Remove files
            for file_path in temp_dir.glob("**/*"):
                if file_path.is_file():
                    file_path.unlink(missing_ok=True)

            # Remove directories in reverse order
            for dir_path in sorted(
                temp_dir.glob("**/*"), key=lambda p: len(p.parts), reverse=True
            ):
                if dir_path.is_dir():
                    dir_path.rmdir()

            # Remove root directory
            if temp_dir.exists():
                temp_dir.rmdir()
        except Exception as e:
            logger.error(f"Error while cleaning: {e}")
