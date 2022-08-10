import zipfile
from pathlib import Path
from prefect import flow, task
from pyfiglet import figlet_format

from sister.storage import InMemoryArchiveStorage
from sister.archive import ArchiveService


@task(name="Prepare the welcome message")
def make_message(message: str):
    formatted_message = figlet_format(message)
    print(f"Current path: {Path.cwd()}")
    return formatted_message


@task(name="Prepare a fake zip file")
def make_zipfile(filename: str = None):
    with zipfile.ZipFile(Path.cwd() / "libs/src/sister/tests/sample.zip", mode="w") as archive:
        for file_path in Path("libs/src/sister/tests/data/").iterdir():
            if file_path.suffix:
                archive.write(file_path, arcname=file_path.name)
        yield archive.filename


def create_inmemory_archive(archive: str):
    zip_file = zipfile.ZipFile(archive)
    archive_service = ArchiveService(
        name="mock_archive",
        zip_file=zip_file,
        archive_storage=InMemoryArchiveStorage()
    )
    archive_service.store()
    tmp_location = archive_service._archive_storage._location
    return tmp_location


@flow
def sister_pipeline(msg: str):
    message = make_message(message=msg)
    print(message)
    zip_file = make_zipfile()
    print(zip_file[0])
    inmemorydir = create_inmemory_archive(archive=zip_file[0])
    print(inmemorydir)


if __name__ == "__main__":
    sister_pipeline(msg="Welcome to Sister")