from prefect.deployments import Deployment

#import the demo script
from flows.demo import prefect_flow
from prefect_aws.s3 import S3Bucket
from prefect_aws.credentials import MinIOCredentials
from prefect_aws.client_parameters import AwsClientParameters
# from prefect.filesystems import RemoteFileSystem

# prefect flows storage
try:
    minio_creds = MinIOCredentials.load("minio-admin") 
except Exception:
    minio_creds = MinIOCredentials(
        minio_root_user="minioadmin",
        minio_root_password="minioadmin",
        aws_client_parameters=AwsClientParameters(endpoint_url="http://minio:9000"),
    )
# s3_client = minio_creds.get_boto3_session().client(
#     service="s3",
#     endpoint_url="http://minio:9000"
# )

try:
    storage = S3Bucket.load("prefect-storage")
    # storage = RemoteFileSystem.load("prefect-storage")
except Exception:
    # storage = RemoteFileSystem(
    #     basepath="s3://prefect-flows",
    #     settings={
    #         "key": "yboS9HPTtenwJJvFDHZR",
    #         "secret": "NbhWKyFNdE8CWaXaYdyhoOmuTN1ik1G3rPFkalOr",
    #         "client_kwargs": {"endpoint_url": "http://minio:9000"}
    #     }
    # )
    storage = S3Bucket(
        bucket="prefect-flows",
        credentials=minio_creds,
    )
    # save a pre-defined block "prefect-storage"
    storage.save("prefect-storage")

# prefect deployment
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
