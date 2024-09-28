import time
from datetime import datetime

from fs import open_fs
from loguru import logger
from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from smidt.client import FTPClient
from smidt.models import EventFile, EventTypeEnum

from .config import settings


class FTPEventHandler(FileSystemEventHandler):
    def __init__(self, ftp_fs):
        self.ftp_fs = ftp_fs
        self.last_read = None
        self.client = None

    def dispatch(self, event):
        super().dispatch(event)
        if event.is_directory:
            return
        logger.info(f"FTP Event: {event.event_type} - {event.src_path.filename}")
        self.client.writetext(
            f"{settings.basepath}/{settings.event_filename}",
            str(datetime.now().timestamp()).split(".")[0],
        )
        self.client.driver.close()
        return event


class FTPPollingObserver(PollingObserver):
    def __init__(self, ftp_url, event_handler, interval=20):
        super().__init__(interval)
        self.ftp_fs = open_fs(ftp_url)
        self.event_handler = event_handler
        self.is_running = False

    def _generate_events(self, event):
        # Check for new/modified files on the FTP server and generate events
        current_files = [
            EventFile(
                event_type=None,
                date_time=datetime.strptime(
                    file_info.get("ftp", "ls")[0:17], "%m-%d-%y  %I:%M%p"
                ),
                filename=file_info.name,
            )
            for file_info in self.ftp_fs.scandir(".")
        ]
        # last_files = self.event_handler.file_paths or []
        # breakpoint()

        # new_files = current_files - last_files
        last_timestamp = self.event_handler.client.readtext(
            f"{settings.basepath}/{settings.event_filename}"
        )
        self.event_handler.last_read = datetime.fromtimestamp(int(last_timestamp))
        self.event_handler.client.driver.close()
        new_file_events = [
            current_file
            for current_file in current_files
            if current_file.date_time >= self.event_handler.last_read
        ]
        # TODO: Handle modified files from current_files
        # modified_files = current_files.intersection(last_files)

        for new_file_event in new_file_events:
            if new_file_event.filename.endswith(".enc"):
                new_file_event.event_type = EventTypeEnum.created
                self.event_handler.dispatch(FileCreatedEvent(new_file_event))

        # for modified_file in modified_files:
        # self.event_handler.dispatch(FileModifiedEvent(modified_file))

        # self.event_handler.file_paths = current_files

    def start(self):
        if not self.is_running:
            super().start()
            self.is_running = True
            self.unlock()
            self._run()

    def stop(self):
        if self.is_running:
            super().stop()
            self.is_running = False
            self.lock()

    def lock(self):
        pass

    def unlock(self):
        pass

    def _run(self):
        while self.should_keep_running():
            # Generate events
            self._generate_events(None)
            time.sleep(self.timeout)


# Example usage
class MyFTPEventHandler(FTPEventHandler):
    def __init__(self, ftp_fs, ftp_client: FTPClient):
        super().__init__(ftp_fs)
        # self.file_paths = []
        self.client = ftp_client
        timestamp = self.client.readtext(
            filepath=f"{settings.basepath}/{settings.event_filename}"
        )
        self.last_read = datetime.fromtimestamp(int(timestamp))
        self.client.driver.close()
