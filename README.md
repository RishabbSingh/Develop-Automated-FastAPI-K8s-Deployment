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

   ```python

   from fastapi import FastAPI, HTTPException

   from kubernetes import client, config

   from pydantic import BaseModel

   import requests

   app = FastAPI()

   # Load the in-cluster config

   config.load_kube_config()

   # Define a Pydantic model for the deployment name

   class DeploymentName(BaseModel):

       name: str

   # Initialize the Kubernetes API client

   k8s_client = client.AppsV1Api()

   # Prometheus URL (replace with your actual Prometheus URL within the cluster)

   PROMETHEUS_URL = "http://your-prometheus-url:9090"

   @app.post("/createDeployment/{deployment_name}")

   def create_deployment(deployment_name: str):

       # Define the deployment spec

       deployment_spec = {

           "apiVersion": "apps/v1",

           "kind": "Deployment",

           "metadata": {"name": deployment_name},

           "spec": {

               "replicas": 1,

               "selector": {"matchLabels": {"app": deployment_name}},

               "template": {

                   "metadata": {"labels": {"app": deployment_name}},

                   "spec": {

                       "containers": [

                           {

                               "name": deployment_name,

                               "image": "nginx",  # Example image

                               "ports": [{"containerPort": 80}],

                           }

                       ]

                   },

               },

           },

       }

       try:

           # Create the deployment

           k8s_client.create_namespaced_deployment(

               namespace="default", body=deployment_spec

           )

           return {"message": f"Deployment {deployment_name} created successfully"}

       except client.exceptions.ApiException as e:

           raise HTTPException(status_code=400, detail=str(e))

   @app.get("/getPromdetails")

   def get_prom_details():

       try:

           # Query Prometheus for running pods

           query = 'up{job="kubernetes-pods"}'

           response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})

           response.raise_for_status()

           return response.json()

       except requests.exceptions.RequestException as e:

           raise HTTPException(status_code=500, detail=str(e))

   ```

2\. **Create `requirements.txt`**

   ```text

   fastapi

   uvicorn

   kubernetes

   pydantic

   requests

   ```

#### 3. **Containerize the Application**

1\. **Create `Dockerfile`**

   ```dockerfile

   # Use the tiangolo/uvicorn-gunicorn-fastapi image as the base image

   FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

   # Set the working directory

   WORKDIR /app

   # Copy the requirements file into the container

   COPY ./requirements.txt /app/requirements.txt

   # Install the dependencies

   RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

   # Copy the FastAPI application code into the container

   COPY ./main.py /app/main.py

   # Command to run the FastAPI application

   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

   ```

2\. **Build the Docker Image**

   ```bash

   docker build -t fast-api-image .

   ```

3\. **Tag the Docker Image**

   ```bash

   docker tag fast-api-image your-dockerhub-username/fast-api-image:latest

   ```

4\. **Push the Docker Image**

   ```bash

   docker push your-dockerhub-username/fast-api-image:latest

   ```

#### 4. **Setup Kubernetes Resources**

1\. **Create a Service Account, Role, and Role Binding**

   Create a YAML file `service-account.yaml`:

   ```yaml

   apiVersion: v1

   kind: ServiceAccount

   metadata:

     name: fastapi-sa

     namespace: default

   ---

   apiVersion: rbac.authorization.k8s.io/v1

   kind: Role

   metadata:

     namespace: default

     name: fastapi-role

   rules:

   - apiGroups: [""]

     resources: ["pods"]

     verbs: ["get", "list"]

   - apiGroups: ["apps"]

     resources: ["deployments"]

     verbs: ["create", "get", "list"]

   ---

   apiVersion: rbac.authorization.k8s.io/v1

   kind: RoleBinding

   metadata:

     name: fastapi-rolebinding

     namespace: default

   subjects:

   - kind: ServiceAccount

     name: fastapi-sa

     namespace: default

   roleRef:

     kind: Role

     name: fastapi-role

     apiGroup: rbac.authorization.k8s.io

   ```

   Apply the file:

   ```bash

   kubectl apply -f service-account.yaml

   ```

2\. **Create Deployment and Service**

   Create a `deployment.yaml`:

   ```yaml

   apiVersion: apps/v1

   kind: Deployment

   metadata:

     name: fastapi-deployment

   spec:

     replicas: 1

     selector:

       matchLabels:

         app: fastapi

     template:

       metadata:

         labels:

           app: fastapi

       spec:

         serviceAccountName: fastapi-sa

         containers:

         - name: fastapi

           image: your-dockerhub-username/fast-api-image:latest

           ports:

           - containerPort: 80

           volumeMounts:

           - name: kubeconfig-volume

             mountPath: /root/.kube

         volumes:

         - name: kubeconfig-volume

           hostPath:

             path: /home/ec2-user/.kube

             type: Directory

   ```

   Apply the file:

   ```bash

   kubectl apply -f deployment.yaml

   ```

3\. **Create a `service.yaml`:**

   ```yaml

   apiVersion: v1

   kind: Service

   metadata:

     name: fastapi-service

   spec:

     selector:

       app: fastapi

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

   Note the external IP from the service output.

#### 6. **Test the FastAPI Endpoints**

1\. **Create Deployment Endpoint**

   ```bash

   curl -X POST "http://<external-ip>/createDeployment/test-deployment"

   ```

2\. **Get Prometheus Details Endpoint**

   ```bash

   curl -X GET "http://<external-ip>/getPromdetails"

   ```

### Summary

By following these steps, you've successfully:

1\. Set up a Kubernetes configuration.

2\. Prepared a FastAPI application.

3\. Containerized the application.

4\. Pushed the Docker image to a container registry.

5\. Created and applied Kubernetes resources.

6\. Verified the deployment and service.

7\. Tested the FastAPI endpoints.

This comprehensive guide ensures that your FastAPI application is running in a Kubernetes cluster, capable of creating deployments and fetching Prometheus details automatically.
