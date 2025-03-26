from prefect.deployments import Deployment

#import the demo script
from flows.demo import prefect_flow
from prefect.filesystems import RemoteFileSystem

# prefect flows storage
try:
    storage = RemoteFileSystem.load("prefect-storage")
except Exception:
    storage = RemoteFileSystem(
        basepath="s3://prefect-flows",
        settings={
            "key": "yboS9HPTtenwJJvFDHZR",
            "secret": "NbhWKyFNdE8CWaXaYdyhoOmuTN1ik1G3rPFkalOr",
            "client_kwargs": {"endpoint_url": "http://minio:9000"}
        }
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
    tags=["catasto"],
    schedule=None,  # (CronSchedule(cron="0 7 * * *", timezone="Africa/Nairobi")),
    work_queue_name="default",
    work_pool_name="default-agent-pool",
)
deploy_demo.apply()
