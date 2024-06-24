# Develop-Automated-FastAPI-K8s-Deployment

Below is a step-by-step documentation on how we have Develop and deployed the automatice K8s Deployment using FastAPI, including setting up a service account, defining roles, and creating a role binding for automatic deployment creation.

## Documentation for Task 2

### Prerequisites

- AWS EKS Cluster set up and running

- `kubectl` configured to interact with your EKS Cluster

- `docker` installed and configured

- `aws-cli` installed and configured

### Step-by-Step Guide

#### 1. **Setup Kubernetes Configuration**

Make sure your Kubernetes configuration is set up correctly.

```bash

export KUBECONFIG=/home/ec2-user/.kube/config

```

Verify your configuration by running:

```bash

kubectl get nodes

```

#### 2. **Prepare FastAPI Application**

Create a FastAPI application with the necessary endpoints.

1\. **Create `main.py`**

```bash
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
```

          
2\. **Create `requirements.txt`**

```bash

   fastapi

   uvicorn

   kubernetes

   pydantic

   requests

```


#### 3. **Containerize the Application**

1\. **Create `Dockerfile`**

 ```bash
 # Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Install the dependencies
RUN pip install --no-cache-dir fastapi uvicorn kubernetes

# Copy the current directory contents into the container at /app
COPY main.py main.py

# Run uvicorn with our FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"] 

   
```

2\. **Build the Docker Image**

```bash

docker build -t api-service .

```

3\. **Tag the Docker Image**

```bash

docker tag api-service rishabsingh12/api-service:v4

```

4\. **Push the Docker Image**

```bash

docker push your-dockerhub-username/api-service:v4

```

#### 4. **Setup Kubernetes Resources**

1\. **Create a Service Account, Role, and Role Binding**

     Create a Individual YAML file of `api-service-account.yaml`, `api-deployment-manager-role.yaml`, `api-deployment-manager-rolebinding.yaml`:

```bash
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-service-account
  namespace: default
```
```bash
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: api-eployment-manager
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "list"]
```
```bash
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: api-deployment-manager-rolebinding
  namespace: default
subjects:
- kind: ServiceAccount
  name: api-service-account
  namespace: default
roleRef:
  kind: Role
  name: api-eployment-manager
  apiGroup: rbac.authorization.k8s.io

```

   Apply the files:

```bash

   kubectl apply -f service-account.yaml

```
```bash

   kubectl apply -f api-deployment-manager-role.yaml

```
```bash

   kubectl apply -f api-deployment-manager-rolebinding.yaml

```

2\. **Create Deployment and Service**

   Create a `deployment.yaml`:

```bash
 apiVersion: apps/v1
kind: Deployment
metadata:
  name: fast-api-python
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fastapi-python
  template:
    metadata:
      labels:
        app: fastapi-python
    spec:
      serviceAccountName: api-service-account
      containers:
      - name: fastapi-python
        image: rishabsingh12/api-service:v4
        ports:
        - containerPort: 80  
```
   
Apply the file:

```bash
   kubectl apply -f deployment.yaml
```

3\. **Create a `service.yaml`:**

```bash
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service-python
spec:
  selector:
    app: fastapi-python
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: LoadBalancer

```
Apply the file:

```bash

   kubectl apply -f service.yaml
```

#### 5. **Verify the Deployment and Service**

1\. **Check the Pods**

```bash

   kubectl get pods

```

2\. **Check the Service**

```bash

   kubectl get svc

```

3\. **Get the External IP**
   
- Copy the external IP from the service output (fastapi-service-python).
- Run this URL added /docs to access fastapi WEBUI a13fd2538294a414ba2a22974aa6466e-1509821416.ap-south-1.elb.amazonaws.com/docs 
```bash
NAME                    TYPE           CLUSTER-IP       EXTERNAL-IP                                                                 PORT(S)        AGE
            
fastapi-service-python   LoadBalancer   10.100.218.238   a13fd2538294a414ba2a22974aa6466e-1509821416.ap-south-1.elb.amazonaws.com   80:32060/TCP   2d8h
kubernetes               ClusterIP      10.100.0.1       <none>                                                                     443/TCP        2d8h
            
```

#### 6. **Test the FastAPI Endpoints**

1\. **POST - It will Create Deployment by the requested name**  

```bash

curl -X 'POST' \
'http://a13fd2538294a414ba2a22974aa6466e-1509821416.ap-south-1.elb.amazonaws.com/createDeployment/<give-deployment-name-here>'

```

2\. **GET - It will display oall deployments which we have created**

```bash

curl -X 'GET' \
'http://a13fd2538294a414ba2a22974aa6466e-1509821416.ap-south-1.elb.amazonaws.com/deployments'

```
