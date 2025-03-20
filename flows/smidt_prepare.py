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
    """Context manager per creare e gestire una directory temporanea"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        pass  # Manteniamo i file, verrà pulito dal sistema


@task
def group_files(lista_file: List[str]) -> Dict[str, Tuple[str, ...]]:
    """
    Task che ordina i file secondo i criteri specificati e li raggruppa per estensione.

    Args:
        lista_file: Lista di percorsi file da ordinare

    Returns:
        Dict[str, Tuple[str, ...]]: Dizionario con estensioni come chiavi e tuple di percorsi ordinati come valori
    """
    logger = get_run_logger()
    logger.info(f"Ordinamento di {len(lista_file)} file")

    # Dizionario per raggruppare i file per estensione
    file_per_estensione = {}

    for percorso_file in lista_file:
        # Converti in Path e poi di nuovo in string con forward slashes
        percorso = Path(percorso_file).as_posix()

        # Separare il percorso in parti
        parti = percorso.split("/")

        # Estrarre le componenti rilevanti
        nome_completo = parti[-1]  # H501189146.Tit o H501A189149.Tit ecc.
        nome_parti = nome_completo.split(".")
        nome_file = nome_parti[0]  # H501189146 o H501A189149 ecc.
        estensione = nome_parti[1]  # Tit, Fab, Prm, Sog, Ter

        # Estrarre l'identificativo (RM000189149022025)
        id_completo = parti[-2]  # RM000189149022025

        # Estrarre data (022025 -> mese 02, anno 2025)
        ultimi_sei = id_completo[-6:]
        mese = ultimi_sei[:2]
        anno = ultimi_sei[2:]

        # Estrarre il numero (000189149)
        numero_id = int(id_completo[2:-6])

        # Estrarre codice comune (H501) e resto del nome file
        codice_comune = nome_file[:4]
        resto_nome = nome_file[4:]

        # Determinare se c'è un carattere alfabetico nel resto del nome
        prefisso_alfa = ""
        num_resto = resto_nome

        for char in resto_nome:
            if char.isalpha():
                # Posizione del carattere alfabetico
                pos = resto_nome.find(char)
                prefisso_alfa = resto_nome[pos]
                # Il resto è il numero
                num_resto = resto_nome.replace(char, "")
                break

        # Convertire la parte numerica in intero
        num_resto = int(num_resto)

        # Chiave di ordinamento: (anno, mese, numero_id, prefisso_alfa, num_resto)
        chiave_ordinamento = (anno, mese, numero_id, prefisso_alfa, num_resto)

        # Aggiungere al dizionario raggruppato per estensione
        if estensione not in file_per_estensione:
            file_per_estensione[estensione] = []

        file_per_estensione[estensione].append((chiave_ordinamento, percorso))

    # Ordinare ogni gruppo e creare tuple di risultati
    risultati = {}
    for estensione, file_list in file_per_estensione.items():
        # Ordinare per la chiave di ordinamento
        file_ordinati = sorted(file_list, key=lambda x: x[0])
        # Estrarre solo i percorsi file (seconda parte della tupla)
        percorsi_ordinati = tuple(item[1] for item in file_ordinati)
        risultati[estensione.upper()] = percorsi_ordinati

        logger.info(
            f"Estensione .{estensione.upper()}: {len(percorsi_ordinati)} file ordinati"
        )

    return risultati


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
        # Itera per ogni estensione e lista di file
        for estensione, file_list in grouped_files.items():
            local_files = []

            # Scarica ogni file
            for file_path in file_list:
                # Converti in Path e ottieni parti del percorso
                remote_path = Path(file_path).as_posix()

                # Crea la struttura di directory locale
                local_path_parts = remote_path.split("/")
                file_name = local_path_parts[-1]
                dir_structure = "/".join(local_path_parts[:-1])

                # Crea la directory locale con la stessa struttura
                local_dir = temp_dir / dir_structure
                local_dir.mkdir(parents=True, exist_ok=True)

                # Percorso locale completo
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
                    # Aggiungi comunque il percorso locale (potrebbe essere necessario per la gestione degli errori)
                    local_files.append(str(local_file_path))

            # Aggiungi al dizionario come tuple
            local_grouped_files[estensione] = tuple(local_files)
            logger.info(
                f"Scaricati {len(local_files)} file con estensione .{estensione}"
            )

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
        lista_file: Lista di percorsi file da ordinare
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
