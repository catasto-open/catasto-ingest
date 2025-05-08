from typing import Protocol

from ftputil import FTPHost
from ftputil.file import FTPFile


class Driver(Protocol):
    """Protocol defining expected interface for FTP drivers."""

    def open(self, filepath: str, mode: str = "r") -> FTPFile: ...

    def close(self) -> None: ...


class Client(Protocol):
    """Protocol defining expected interface for FTP clients."""

    driver: Driver

    def readtext(self, filepath: str) -> str: ...


class FTPConfig:
    """FTP configuration class with required attributes."""

    def __init__(self, host: str, user: str, password: str):
        self.HOST = host
        self.USER = user
        self.PASSWORD = password


class FTPDriver(Driver):
    """FTP driver implementation."""

    def __init__(self, config: FTPConfig, connection: FTPHost = None):
        self.connection = connection
        self.config = config

    def open(self, filepath: str, mode: str = "r") -> FTPFile:
        self.connection = FTPHost(
            self.config.HOST,
            self.config.USER,
            self.config.PASSWORD,
        )
        return self.connection.open(filepath, mode)

    def close(self) -> None:
        if self.connection:
            self.connection.close()


class FTPClient(Client):
    """FTP client implementation."""

    def __init__(self, driver: Driver):
        self.driver = driver

    def readtext(self, filepath: str) -> str:
        resource = self.driver.open(filepath)
        return resource.readline()

    def writetext(self, filepath: str, content: str) -> None:
        resource = self.driver.open(filepath, mode="w")
        resource.write(content)
