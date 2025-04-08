import os
import tempfile
import time
from datetime import datetime
from typing import List, Set, Tuple

from ftputil import FTPHost
from loguru import logger
from minio import Minio
from minio.error import S3Error

from smidt.client import FTPClient, FTPConfig, FTPDriver
from smidt.models import EventFile, EventTypeEnum, TransferredFile

# Configure logging
logger.remove()
logger.add(
    "ftp_observer_{time}.log",
    rotation="1 day",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG",
)
logger.add(
    lambda msg: print(msg),
    format="{time:HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG",
    colorize=True,
)


class FTPMinioObserver:
    """
    Monitors FTP directory for new files and backs them up to MinIO.
    Uses FTP client for file operations and MinIO for storage.
    """

    def __init__(
        self,
        ftp_config: FTPConfig,
        remote_dir: str,
        lock_filename: str,
        minio_endpoint: str,
        minio_access_key: str,
        minio_secret_key: str,
        minio_bucket: str,
        minio_secure: bool = True,
    ):
        """Initialize the observer with FTP and MinIO configurations."""
        self.config = ftp_config
        self.remote_dir = remote_dir
        self.lock_filename = lock_filename
        self._known_files: Set[str] = set()

        # Initialize MinIO client
        self.minio_client = Minio(
            endpoint=minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=minio_secure,
        )
        self.minio_bucket = minio_bucket

        # Ensure MinIO bucket exists
        self._ensure_minio_bucket()

    def _ensure_minio_bucket(self):
        """Create MinIO bucket if it doesn't exist and verify permissions."""
        try:
            if not self.minio_client.bucket_exists(self.minio_bucket):
                self.minio_client.make_bucket(self.minio_bucket)
                logger.info(f"Created MinIO bucket: {self.minio_bucket}")

            # Test permissions
            self.minio_client.list_objects(
                self.minio_bucket, prefix="", recursive=False
            )
            logger.debug(f"Verified access to bucket: {self.minio_bucket}")

        except S3Error as e:
            if "AccessDenied" in str(e):
                raise S3Error(
                    f"Insufficient permissions for bucket {self.minio_bucket}"
                )
            raise

    def read_lock_file(self) -> datetime | None:
        """Read timestamp from lock file using FTP client."""
        driver = None
        try:
            driver = FTPDriver(self.config)
            client = FTPClient(driver)

            lock_path = f"{self.remote_dir}/{self.lock_filename}".replace("//", "/")
            content = client.readtext(lock_path)
            timestamp = float(content)  # Direttamente il valore numerico

            logger.debug(
                f"Read lock timestamp: {str(datetime.fromtimestamp(timestamp))}"
            )
            return timestamp

        except Exception as e:
            logger.warning(f"Failed to read lock file: {e}")
            return None
        finally:
            if driver:
                driver.close()

    def update_lock_file(self, timestamp: float):
        """Update timestamp in lock file using FTP client."""
        driver = None
        try:
            driver = FTPDriver(self.config)
            client = FTPClient(driver)

            lock_path = f"{self.remote_dir}/{self.lock_filename}".replace("//", "/")
            content = str(timestamp)  # Solo il valore numerico
            client.writetext(lock_path, content)

            logger.debug(f"Updated lock timestamp: {datetime.fromtimestamp(timestamp)}")
        finally:
            if driver:
                driver.close()

    def list_files(self) -> List[Tuple[str, datetime]]:
        """List files in monitored directory with their timestamps."""
        driver = None
        try:
            driver = FTPDriver(self.config)
            connection = FTPHost(
                self.config.HOST,
                self.config.USER,
                self.config.PASSWORD,
            )

            files = []
            for name in connection.listdir(self.remote_dir):
                if connection.path.isfile(f"{self.remote_dir}/{name}"):
                    stat = connection.stat(f"{self.remote_dir}/{name}")
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    files.append((name, mtime))

            return files

        finally:
            if driver:
                driver.close()

    def detect_events(self) -> List[EventFile]:
        """Detect file creation and modification events."""
        current_files = set()
        events = []

        for name, mtime in self.list_files():
            current_files.add(name)

            if name not in self._known_files:
                events.append(
                    EventFile(
                        event_type=EventTypeEnum.created, date_time=mtime, filename=name
                    )
                )

        self._known_files = current_files
        return events

    def backup_to_minio(self, event: EventFile) -> bool:
        """Back up a file to MinIO using FTP download."""
        temp_file = None
        connection = None
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode="wb", delete=False)
            temp_file.close()

            # Download file using FTP
            file_path = f"{self.remote_dir}/{event.filename}".replace("//", "/")
            connection = FTPHost(
                self.config.HOST,
                self.config.USER,
                self.config.PASSWORD,
            )
            connection.download(file_path, temp_file.name, "b")

            # Get file size
            file_size = os.path.getsize(temp_file.name)

            # Upload to MinIO
            minio_path = f"{datetime.now().strftime('%Y/%m/%d')}/{event.event_type.value}/{event.filename}"
            with open(temp_file.name, "rb") as f:
                self.minio_client.put_object(
                    bucket_name=self.minio_bucket,
                    object_name=minio_path,
                    data=f,
                    length=file_size,
                )

            logger.info(
                f"Backed up {event.filename} ({file_size} bytes) to MinIO: {minio_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to backup {event.filename}: {e}")
            return False

        finally:
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass
            if connection:
                connection.close()

    def process_events(
        self,
    ) -> Tuple[List[EventFile], List[EventFile], List[TransferredFile]]:
        """
        Process detected events and back up new files.

        Returns:
            Tuple containing:
            - List of detected events
            - List of successfully processed events
            - List of MinIO paths where files were stored
        """
        current_time = time.time()
        last_check_time = self.read_lock_file()
        transferred_files = []

        if last_check_time is None:
            last_check_time = current_time

        # Detect and filter events
        events = self.detect_events()
        filtered_events = []
        processed_events = []

        for event in events:
            if event.filename == self.lock_filename:
                continue

            if event.event_type != EventTypeEnum.created:
                continue

            if event.date_time.timestamp() > last_check_time:
                filtered_events.append(event)

        # Process filtered events
        if filtered_events:
            logger.info(f"Processing {len(filtered_events)} new files")

            for event in filtered_events:
                minio_path = f"{datetime.now().strftime('%Y/%m/%d')}/{event.event_type.value}/{event.filename}"
                if self.backup_to_minio(event):
                    processed_events.append(event)

                    # Get file size if available
                    try:
                        file_path = f"{self.remote_dir}/{event.filename}".replace(
                            "//", "/"
                        )
                        connection = FTPHost(
                            self.config.HOST, self.config.USER, self.config.PASSWORD
                        )
                        size = connection.path.getsize(file_path)
                        connection.close()
                    except Exception:
                        size = None

                    transferred_files.append(
                        TransferredFile(
                            filename=event.filename,
                            timestamp=event.date_time,
                            minio_path=minio_path,
                            bucket=self.minio_bucket,
                            size=size,
                            event_type=event.event_type,
                        )
                    )

            if processed_events:
                self.update_lock_file(current_time)

        return filtered_events, processed_events, transferred_files

    def start_monitoring(self, interval: int = 60, single_run: bool = False):
        """
        Start monitoring of the FTP directory.

        Args:
            interval: Number of seconds between checks
            single_run: If True, executes only one check and returns
        """
        logger.info(f"Starting monitoring of directory: {self.remote_dir}")
        logger.info(f"Backup configured to MinIO bucket: {self.minio_bucket}")
        logger.info(f"Mode: {'single run' if single_run else 'continuous'}")

        try:
            while True:
                events, processed_events, transferred_files = self.process_events()

                if events:
                    for event in events:
                        logger.info(str(event))

                    if len(processed_events) < len(events):
                        failed = [e for e in events if e not in processed_events]
                        for event in failed:
                            logger.warning(f"Failed to process: {str(event)}")

                    if transferred_files:
                        logger.info("Files transferred in this interval:")
                        for transfer in transferred_files:
                            logger.info(f"File: {transfer.filename}")
                            logger.info(
                                f"  Timestamp: {transfer.timestamp.isoformat()}"
                            )
                            logger.info(
                                f"  MinIO Path: {transfer.bucket}/{transfer.minio_path}"
                            )

                # Return the transferred files information
                if transferred_files:
                    yield transferred_files

                # If single_run is True, exit after first check
                if single_run:
                    logger.info("Single run completed")
                    break

                logger.debug(f"Waiting {interval} seconds")
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.warning("Monitoring interrupted by user")
        except Exception as e:
            logger.exception(f"Error during monitoring: {e}")
