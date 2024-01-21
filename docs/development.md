# Development

## How to get started

Let's introduce the journey for developers 🛫 to managing the ingestion process of catasto data.

### Start a complete environment

The repo has batteries included to manage and monitor the workflows to ingest the data into the target
database. A Docker Compose script is provided to start the different components:

- *Prefect* with server and agents
- *Minio* to host the code and data
- A python virtual environment to deploy Prefect flows

#### 