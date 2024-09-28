import time

from fs import open_fs

from smidt.client import FTPClient, FTPConfig, FTPDriver
from smidt.config import settings
from smidt.watcher import FTPPollingObserver, MyFTPEventHandler

ftp_config = FTPConfig()
driver = FTPDriver(config=ftp_config)
ftp_client = FTPClient(driver=driver)

ftp_url = f"ftp://{settings.ftp_user}:{settings.ftp_password.get_secret_value()}@{settings.ftp_host}{settings.basepath}"

event_handler = MyFTPEventHandler(open_fs(ftp_url), ftp_client)
observer = FTPPollingObserver(ftp_url, event_handler)


def __main__():
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
