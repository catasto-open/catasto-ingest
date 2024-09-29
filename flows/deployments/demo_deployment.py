from pathlib import Path

from prefect_aws.client_parameters import AwsClientParameters
from prefect_aws.credentials import MinIOCredentials
from prefect_aws.s3 import S3Bucket

from flows.demo import prefect_flow

# prefect flows storage
try:
    minio_creds = MinIOCredentials.load("minio-admin")
except ValueError:
    minio_creds = MinIOCredentials(
        minio_root_user="minioadmin",
        minio_root_password="minioadmin",
        aws_client_parameters=AwsClientParameters(endpoint_url="http://minio:9000"),
    )
    # save a pre-defined block "minio-admin"
    minio_creds.save("minio-admin")

try:
    storage = S3Bucket.load("prefect-storage")
except ValueError:
    storage = S3Bucket(
        bucket_name="prefect-flows",
        credentials=minio_creds,
    )
    # save a pre-defined block "prefect-storage"
    storage.save("prefect-storage")

# prefect deployment

try:
    flows_dir = Path(__file__).parent.parent
    storage.upload_from_folder(
        str(flows_dir), flows_dir.name
    )
except:
    pass

# create and deploy a prefect deployment
prefect_flow.from_source(
    source=storage, entrypoint="flows/demo.py:prefect_flow"
    ).deploy(
    name="Prefect flow deployment",
    version="1",
    job_variables=dict({"env.PREFECT_LOGGING_LEVEL": "DEBUG"}),
    tags=["demo"],
    schedule=None,
    work_queue_name="default",
    work_pool_name="default",
)
