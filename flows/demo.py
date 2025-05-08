from prefect import task, flow

# Define tasks using the @task decorator
@task(name="extract data", log_prints=True, tags="extract")
def extract_data():
    return [1, 2, 3, 4, 5]

@task(name="transform data", log_prints=True, tags="transform")
def transform_data(data):
    return [x * 2 for x in data]

@task(name="load data", log_prints=True, tags="load")
def load_data(transformed_data):
    print("Transformed Data:", transformed_data)

# Create a flow
@flow(name="prefect flow")
def prefect_flow():
    data = extract_data()
    transformed = transform_data(data)
    load_data(transformed)

if __name__ == "__main__":
    prefect_flow()
