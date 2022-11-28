from prefect import flow, get_run_logger
from prefect.blocks.core import Block
from prefect.blocks.system import String
from prefect_docker.images import pull_docker_image
from prefect_docker.containers import (
    create_docker_container,
    start_docker_container,
    get_docker_container_logs,
    stop_docker_container,
    remove_docker_container,
)


@flow(name="Sister ingestion workflow")
def sister_loader(upload_path: str, filename: str = None):
    logger = get_run_logger()
    dh_block = Block.load("docker-host/dh-local")
    dcr_block = Block.load("docker-registry-credentials/dcr-georoma")
    sister_block = Block.load("remote-file-system/sister")
    network_block = String.load("docker-network")

    network = network_block.value
    key = sister_block.settings["key"]
    secret = sister_block.settings["secret"]
    minio_url = sister_block.settings["client_kwargs"]["endpoint_url"]
    
    if filename:
        transformed_cxf = cs2etrf_flow(
            foldername=upload_path,
            filename=filename,
            docker_host=dh_block,
            docker_registry_credentials=dcr_block,
            network=network,
            minio_url=minio_url,
            key=key,
            secret=secret
        )
        if transformed_cxf:
            logger.info(f"Created CTF transformed file")
    else:
        pass


@flow
def cs2etrf_flow(
    foldername: str,
    filename: str,
    docker_host,
    docker_registry_credentials,
    network,
    minio_url: str,
    key: str,
    secret: str
):
    logger = get_run_logger()
    pull_docker_image(
        repository="geobeyond/etrflib",
        tag="latest",
        docker_host=docker_host,
        docker_registry_credentials=docker_registry_credentials
    )
    container = create_docker_container(
        image="geobeyond/etrflib:latest",
        entrypoint="/bin/bash",
        network=network,
        command=[
            "-c",
            f"etrflib remote-convert --bucket-path {minio_url}/sister --object-path {foldername} --filename {filename}.cxf --destination-path {filename} --key {key} --secret {secret}"
        ]
    )
    start_docker_container(container_id=container.id)
    logs = get_docker_container_logs(container_id=container.id)
    logger.info(logs)
    stop_docker_container(container_id=container.id)
    remove_docker_container(container_id=container.id)
    return container
