from fastapi import FastAPI, HTTPException
from kubernetes import client, config

app = FastAPI()

# Load the Kubernetes configuration
config.load_incluster_config()

# Kubernetes client setup
api_instance = client.AppsV1Api()

@app.post("/createDeployment/{name}")
async def create_deployment(name: str):
    try:
        # Define the deployment
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={"app": name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": name}),
                    spec=client.V1PodSpec(
                        containers=[client.V1Container(
                            name="nginx",
                            image="nginx:latest",
                            ports=[client.V1ContainerPort(container_port=80)]
                        )]
                    )
                )
            )
        )

        # Create the deployment
        api_instance.create_namespaced_deployment(
            namespace="default",
            body=deployment
        )

        return {"message": f"Deployment '{name}' created successfully."}

    except client.exceptions.ApiException as e:
        raise HTTPException(status_code=400, detail=f"Error creating deployment: {e}")

@app.get("/deployments")
async def get_deployments():
    try:
        # Get all deployments in the default namespace
        deployments = api_instance.list_namespaced_deployment(namespace="default")

        deployment_list = [deployment.metadata.name for deployment in deployments.items]
        
        return {"deployments": deployment_list}

    except client.exceptions.ApiException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching deployments: {e}")
