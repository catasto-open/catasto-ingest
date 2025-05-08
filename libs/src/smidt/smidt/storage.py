import time

from fs import open_fs
from ftputil import FTPHost
from ftputil.error import FTPOSError
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class FTPEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        """
        A function that is called when a file or directory is created.

        Args:
            event (FileSystemEvent): The event object that contains information about the created file or directory.

        Returns:
            None
        """
        if event.is_file:
            return
        print(f"New file created: {event.src_path}")


def watch_ftp_directory(ftp_url):
    ftp_fs = open_fs(ftp_url)
    event_handler = FTPEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=ftp_fs.geturl("."), recursive=False)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def watch_ftp_new_files(host, user, password, dir, interval=5):
    with FTPHost(host, user, password) as ftp_host:
        last_files = set()

        try:
            while True:
                current_files = set(ftp_host.listdir(dir))
                new_files = current_files - last_files

                for new_file in new_files:
                    print(f"New file created: {new_file}")

                last_files = current_files
                time.sleep(interval)
        except FTPOSError:
            print("Connection Error with FTP server")
            raise
        except KeyboardInterrupt:
            pass
