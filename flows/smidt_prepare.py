import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Tuple

# Importa la libreria per Minio
import boto3
from botocore.client import Config
from prefect import flow, task
from prefect.logging import get_run_logger


@contextmanager
def temp_directory():
    """Context manager to creare and handle a temporary directory."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        pass  # Maintain the directory, it will be cleaned up when the flow is done


@task
def group_files(files_list: List[str]) -> Dict[str, Tuple[str, ...]]:
    """
    Order and group the files by extension.

    Args:
        files_list: List filepaths to be ordered and grouped.

    Returns:
        Dict[str, Tuple[str, ...]]: Dictionary with extensions as keys and tuples of ordered filepaths as values.
    """
    logger = get_run_logger()
    logger.info(f"Ordering {len(files_list)} files...")

    # Dizionary to group files by extension.
    files_by_extension = {}

    for filepath in files_list:
        # Converti in Path e poi di nuovo in string con forward slashes
        path = Path(filepath).as_posix()

        # Divide the path in parts
        parts = path.split("/")

        # Extract relevant components
        complete_name = parts[-1]  # H501189146.Tit o H501A189149.Tit ecc.
        name_parts = complete_name.split(".")
        filename = name_parts[0]  # H501189146 o H501A189149 ecc.
        extension = name_parts[1]  # Tit, Fab, Prm, Sog, Ter, Sup, Cxf

        # Extract identifier (RM000189149022025)
        complete_id = parts[-2]  # RM000189149022025

        # Extract date (022025 -> month 02, year 2025)
        last_six = complete_id[-6:]
        month = last_six[:2]
        year = last_six[2:]

        # Extract the number (000189149)
        number_id = int(complete_id[2:-6])

        # Extract municipality code and the rest of the file name.
        municipality_code = filename[:4]
        reduced_name = filename[4:]

        # Determine if there is an alphabetical character in the rest of the name and extract it
        alfa_prefix = ""
        numeric_part = reduced_name

        for char_ in reduced_name:
            if char_.isalpha():
                # alphabetic character position
                pos = reduced_name.find(char_)
                alfa_prefix = reduced_name[pos]
                # after there is the number
                numeric_part = reduced_name.replace(char_, "")
                break

        # Convert numeric part to integer
        if extension.upper() in ["FAB", "SOG", "TER", "TIT"]:
            numeric_part = int(numeric_part)
        elif extension.upper() in ["CXF", "SUP"]:
            if numeric_part.isalnum():
                numeric_part = int(numeric_part[:-2])
            else:
                numeric_part = int(numeric_part)

        # Ordering key: (year, month, number_id, alfa_prefix, numeric_part)
        ordering_key = (year, month, number_id, alfa_prefix, numeric_part)

        # Add results to the dictionary by extension type
        if extension not in files_by_extension:
            files_by_extension[extension] = []

        files_by_extension[extension].append((ordering_key, path))

    # Order groups and create result tuples.
    results = {}
    for extension, file_list in files_by_extension.items():
        # Ordering by ordering key
        ordered_files = sorted(file_list, key=lambda x: x[0])
        # Extract only the paths
        ordered_paths = tuple(item[1] for item in ordered_files)
        results[extension.upper()] = ordered_paths

        logger.info(
            f"Extension .{extension.upper()}: {len(ordered_paths)} ordered files"
        )

    return results


@task
def downloaded_grouped_files(
    grouped_files: Dict[str, Tuple[str, ...]],
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    minio_bucket: str,
    secure: bool = True,
    temp_dir: Path = None,
) -> Dict[str, Tuple[str, ...]]:
    """
    Task che scarica i file da un bucket Minio e restituisce i percorsi locali.

    Args:
        grouped_files: Dizionario con estensioni come chiavi e tuple di percorsi come valori
        minio_endpoint: Endpoint del server Minio (es. "minio.example.com:9000")
        minio_access_key: Access key per Minio
        minio_secret_key: Secret key per Minio
        minio_bucket: Nome del bucket Minio
        secure: Se True, usa HTTPS, altrimenti HTTP
        temp_dir: Directory temporanea dove scaricare i file (se None, ne crea una nuova)

    Returns:
        Dict[str, Tuple[str, ...]]: Dizionario con la stessa struttura ma con percorsi locali
    """
    logger = get_run_logger()
    logger.info(f"Inizio download dei file dal bucket Minio: {minio_bucket}")

    # Crea un client Minio usando boto3 (compatibile con S3)
    s3_client = boto3.client(
        "s3",
        endpoint_url=f"{'https' if secure else 'http'}://{minio_endpoint}",
        aws_access_key_id=minio_access_key,
        aws_secret_access_key=minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",  # Parametro fittizio richiesto da boto3
    )

    # Crea la directory temporanea se non fornita
    if temp_dir is None:
        temp_context = temp_directory()
        temp_dir = temp_context.__enter__()
    else:
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_context = None

    logger.info(f"Download dei file nella directory temporanea: {temp_dir}")

    # Dizionario per i nuovi percorsi locali
    local_grouped_files = {}

    try:
        # Itera per ogni extension e lista di file
        for extension, file_list in grouped_files.items():
            local_files = []

            # Scarica ogni file
            for file_path in file_list:
                # Converti in Path e ottieni parts del path
                remote_path = Path(file_path).as_posix()

                # Crea la struttura di directory locale
                local_path_parts = remote_path.split("/")
                file_name = local_path_parts[-1]
                dir_structure = "/".join(local_path_parts[:-1])

                # Crea la directory locale con la stessa struttura
                local_dir = temp_dir / dir_structure
                local_dir.mkdir(parents=True, exist_ok=True)

                # path locale completo
                local_file_path = local_dir / file_name

                # Scarica il file da Minio
                logger.info(f"Download di {remote_path} in {local_file_path}")
                try:
                    s3_client.download_file(
                        Bucket=minio_bucket,
                        Key=remote_path,
                        Filename=str(local_file_path),
                    )
                    local_files.append(str(local_file_path))
                except Exception as e:
                    logger.error(f"Errore nel download di {remote_path}: {str(e)}")
                    # Aggiungi comunque il path locale (potrebbe essere necessario per la gestione degli errori)
                    local_files.append(str(local_file_path))

            # Aggiungi al dizionario come tuple
            local_grouped_files[extension] = tuple(local_files)
            logger.info(f"Scaricati {len(local_files)} file con extension .{extension}")

    except Exception as e:
        logger.error(f"Errore durante il download dei file: {str(e)}")
        raise

    return local_grouped_files


@flow(name="Download and Sort Files Flow")
def download_and_sort_flow(
    files_list: List[str],
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    minio_bucket: str,
    secure: bool = True,
):
    """
    Flusso che ordina i file e li scarica da Minio.

    Args:
        files_list: Lista di percorsi file da ordinare
        minio_endpoint: Endpoint del server Minio
        minio_access_key: Access key per Minio
        minio_secret_key: Secret key per Minio
        minio_bucket: Nome del bucket Minio
        secure: Se True, usa HTTPS, altrimenti HTTP

    Returns:
        Dict[str, Tuple[str, ...]]: Percorsi locali dei file scaricati e raggruppati
    """

    grouped_files = group_files(files_list)

    local_files = downloaded_grouped_files(
        grouped_files=grouped_files,
        minio_endpoint=minio_endpoint,
        minio_access_key=minio_access_key,
        minio_secret_key=minio_secret_key,
        minio_bucket=minio_bucket,
        secure=secure,
    )

    return local_files
