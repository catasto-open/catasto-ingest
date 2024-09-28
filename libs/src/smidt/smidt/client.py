from typing import Protocol

from ftputil import FTPHost
from ftputil.file import FTPFile

from .config import settings


class Driver(Protocol):
    def open(self, filepath: str) -> None:
        pass

    def close(self) -> None:
        pass


class FTPConfig:
    HOST = settings.ftp_host
    USER = settings.ftp_user
    PASSWORD = settings.ftp_password


class Client(Protocol):
    driver: Driver

    def readtext(self) -> str:
        pass


class FTPDriver(Driver):
    def __init__(self, config: FTPConfig, connection: FTPHost = None):
        self.connection = connection
        self.config = config

    def open(self, filepath: str, mode: str = "r") -> FTPFile:
        self.connection = FTPHost(
            self.config.HOST,
            self.config.USER,
            self.config.PASSWORD.get_secret_value(),
        )
        return self.connection.open(filepath, mode)

    def close(self) -> None:
        self.connection.close()


class FTPClient(Client):
    def __init__(self, driver: Driver):
        self.driver = driver

    def readtext(self, filepath: str) -> str:
        resource = self.driver.open(filepath)
        return resource.readline()

    def writetext(self, filepath: str, content: str) -> None:
        resource = self.driver.open(filepath, mode="w")
        resource.write(content)
