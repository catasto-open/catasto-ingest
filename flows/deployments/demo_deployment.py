from prefect.deployments import Deployment

from flows.demo import prefect_flow
from prefect_aws.s3 import S3Bucket
from prefect_aws.credentials import MinIOCredentials
from prefect_aws.client_parameters import AwsClientParameters

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

# create and deploy a prefect deployment
deploy_demo = Deployment.build_from_flow(
    flow=prefect_flow,
    name="Prefect flow deployment",
    version="1",
    storage=storage,
    infra_overrides=dict({"env.PREFECT_LOGGING_LEVEL": "DEBUG"}),
    tags=["demo"],
    schedule=None,
    work_queue_name="default",
    work_pool_name="default-agent-pool",
)
deploy_demo.apply()
