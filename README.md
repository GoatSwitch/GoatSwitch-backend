# GoatSwitch AI

Welcome to Goatswitch. 🐐 🐐

## Installation

Goatswitch requires the following software to be installed on your system:

- Python 3.10 and pip

```
sudo apt install python3-pip
# windows: install w miniconda
```

- dotnet 8

```
sudo apt install dotnet-host-8.0 dotnet-sdk-8.0
# windows: download installer
```

- NVM NPM

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
source ~/.bashrc
nvm install node
# windows: download installer
```

- Docker

```
sudo apt install docker.io
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
# verify running docker without sudo
docker run hello-world
# windows: download docker-desktop; need win11 pro
```

- Dapr CLI

```
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
dapr init
# on windows
dapr init --slim
```

- gs-vault

```
sudo mkdir /mnt/gs-vault
sudo chown -R $USER:$USER /mnt/gs-vault/
```

## NOTE: you also need to read and install src/goat_service/code_executor/README.md

## NOTE: for testing you also need to read and install test/README.md

## Using VertexAI intead of OpenAI

- download your credentials from GCP
  - go to: https://console.cloud.google.com/iam-admin/serviceaccounts?authuser=0&project=goatswitch
  - click goatswitch service accoun
  - generate key as json
  - download json
- set "model" in config.yaml to a PaLM model

```
export GOOGLE_APPLICATION_CREDENTIALS="/home/mw3155/goatswitch-a8cda566739a.json"
pip install google-cloud-aiplatform
```

## Environment Variables Linux

```
# add this to .bashrc
export OPENAI_API_KEY="..."
export AZURE_OPENAI_API_KEY="..."
export PYTHONPATH=.
export AZ_TABLES_CONNECTION_STRING="..."
```

## Environment Variables Windows

```
# open pwoershell profile
notepad $PROFILE

# write this
conda activate gs
$env:NG_CLI_ANALYTICS = 0
$env:PYTHONPATH = "."

$env:OPENAI_API_KEY = "..."
$env:AZURE_OPENAI_API_KEY = "..."
$env:AZ_TABLES_CONNECTION_STRING="..."

# add msbuild to path (must have installed Visual Studio)
$env:Path += ";C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin"
# download nuget.exe and set path
$env:Path += ";C:\nuget"
```

## Building Goatswitch

- needs to be done once before running dapr currently

```
cd src/gateway/API_Gateway/
dotnet publish -r linux-x64 -c Release --sc true
```

## Running Goatswitch

Run the following command to start Goatswitch from the GoatSwitch directory:

```
dapr run -f dapr.yaml
```

## Kubernetes

### Network stuff

Request -> IngressController -> Ingress -> api-gateway (service) -> api-gateway (deployment) -> TLGenerator, Executor, etc...

- IngressController
  - Corresponding service/deployment: nginx-ingress-controller.yaml
  - Can be reached from outside
  - Has the "GS-Cluster-IP" static IP
- Ingress
  - Corresponding service/deployment: api-gateway-ingress.yaml
  - Defines routing rules, e.g. beta.goatswitch.ai -> api-gateway:80
  - Handles SSL stuff (using certbot service)
- api-gateway (service)
  - Corresponding service: api-gateway.yaml
  - Makes api-gateway accessible from "outside", the ingress can reach it
  - defines routing rule: service:80 -> api-gateway:5000
- api-gateway (deployment)
  - Corresponding service: api-gateway.yaml
  - actually api-gateway application docker container
  - IMPORTANT: does not do any SSL stuff, thats handled by the ingress

### Basic commands

```
# check the pods
kubectl get pods --all-namespaces
# check deployments
kubectl get deployments --all-namespaces=true
# Update specific resource in cluster
kubectl apply -f ./deploy/api-gateway.yaml
# Deploy all resources (e.g. after updating them via github action)
kubectl rollout restart deployment -n default
# Status of deployments
kubectl rollout status deploy/api-gateway
```

### Access cluster

Azure cluster needs to be added locally first (instructions taken from azure)

- Prerequisites

```
# Install Azure CLI

curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install kubectl

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install kubelogin
sudo az aks install-cli

```

# Login to your azure account

az login

# Set the cluster subscription

az account set --subscription d410f682-3a81-4f4c-b9f8-f2ce61995fa7

# Download cluster credentials

az aks get-credentials --resource-group GoatSwitchAI_Azuresponsored --name GoatSwitchCluster2

# Use kubelogin plugin for authentication

kubelogin convert-kubeconfig -l azurecli

```

From here the cluster is usable locally

```

kubectl get deployments --all-namespaces=true

# restart all in default namespace

kubectl rollout restart deployment -n default

```

Proxy-dashboard cluster 1

```

# proxy for something?

kubectl proxy

# Forward port from inside to outside

kubectl port-forward service/api-gateway 8080:80 5050:5050

```

Proxy-dashboard cluster 2
( add to contexts if not already done & siwtch to it like explaine in ### Siwtch Clusters )

```

az aks get-credentials --resource-group GoatSwitchAI_Azuresponsored --name GoatSwitchCluster2

```

Somehow proxing using the general way doesnt work anymore, so this is the way now:

```

# get token for login

kubectl -n kubernetes-dashboard create token admin-user

# forward port

kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443

```

dashbaord is exposed on https://localhost:8443/#/, login via token from above

### Switch Clusters

```

# Get available kubectl contexts, usefull for switching between azure and local minikube

kubectl config get-contexts
kubectl config use-context minikube

```

### Push docker image to azure container registry

```

az acr login --name goatswitch
docker tag goatswitch_goat_service goatswitch.azurecr.io/goatswitch_goat_service:latest
docker push goatswitch.azurecr.io/goatswitch_goat_service:latest

```

### Minikube

Minikube is a local kubernetes cluster useful for testing and developing

```

# Start/stop cluster

minikube stop
minikube start
minikube dashboard
#Connect minikube docker with current shell (minikube can only access containers build within its own docker)
eval $(minikube docker-env)

# build all dockerfiles locally

bash build_all.sh

# init dapr

dapr init -k # !!only do this locally, install via helm on azure, see HowToNewCluster.md for reference

# deploy all services

kubectl apply -f ./deploy_local/

# redeploy one service after changing code

kubectl rollout restart deployments/code_executor

# check deployments

kubectl get deployments --all-namespaces=true

# forward ports and go to localhost:8080

kubectl port-forward service/api-gateway 8080:80 5050:5050

# delete all services in a namespace

kubectl delete deployments --all -n default

```

## Certmanager

Provides SSL-certificates
Is relatec to clusterissuer.yaml

```

# Certmanager auf kubernetes

kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.9.1/cert-manager.yaml

```

## Opentelemetry-collector

The otel-collector collects all the logs from containers.
It runs as a daemonset and as such has 1 instance running on every cluster node.
A single collector does two things:

1. Collect logs from stdout etc. of all containers on the node
2. Collect traces from all services on the node
   After collections things are sent to wherever is specified in the config, e.g. traces are sent to the central zipkin instance.

Installation is done via helm charts:

```

helm install --namespace=dapr-monitoring otel-collector open-telemetry/opentelemetry-collector --values helm-values/otel-values.yaml

```

## Prometheus

```

helm install dapr-prom prometheus-community/prometheus -n dapr-monitoring --values helm-values/prometheus-values.yaml

```

## Loki

Loki aggregates logs and makes them searchable. Installation is done via helm charts:

```

helm install --namespace=dapr-monitoring loki grafana/loki --values helm-values/loki-values.yaml

```
## Grafana Tempo

```

helm install --namespace=dapr-monitoring tempo grafana/tempo --values helm-values/tempo-values.yaml

```

## Zipkin

Zipkin is used to collect traces. The traces are first collected by the otel-collector daemonset and then sent to zipkin.
Configuration is done via deploy/zipkin.yaml
(https://docs.dapr.io/operations/observability/tracing/zipkin/)

## Grafana

Grafana is a GUI for displaying charts tables etc.
GoatSwitch Grafana can be reached on https://grafana.goatswitch.ai for cluster 1 and
on https://grafana2.goatswitch.ai for cluster 2.
Grafana has its own ingress so that its available on the above link.
Authentication is done using Google OAuth

### Install & Maintanance

Grafana is installed using Helm charts, therefore it has no yaml in deploy/, everything is configured at install.
The install includes a deployment and a corresponding service to access it.

```

helm install --namespace dapr-monitoring grafana grafana/grafana --values helm-values/grafana-values.yaml

# Admin account password in GUI (User: admin)

kubectl get secret --namespace dapr-monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo

```

### Connection Settings

Zipkin

```

URL: http://zipkin.dapr-monitoring:9411
Data Source: Loki
tags
k8s.namespace.name as k8s_namespace_name
k8s.pod.name as k8s_pod_name
trace_id
Skip TLS Certificate validation

```

Loki

```

URL: http://loki.dapr-monitoring:3100
Skip TLS Certificate validation

```

Dapr (Prometheus data source)
Skip TLS Certificate validation

```

Prometheus server url: http://dapr-prom-prometheus-server.dapr-monitoring

```

## Azure File Storage via ACI

(https://learn.microsoft.com/en-us/azure/aks/azure-csi-files-storage-provision)
Note: This is not blob storage, blob doesnt work for windows containers.
azure-file-sc-gs-vault.yaml defines a pvc (persistant volume claim) that pods can mount and use
concurrently.

## vscode extension problems

- vscode extension running on windows cannot connect to localhost on wsl (since 2024-03-31)
- "solution": permanenty port forward with powershell admin:

```

netsh interface portproxy add v4tov4 listenport=5012 listenaddress=0.0.0.0 connectport=5012 connectaddress=172.28.215.114

```

## Dev setup

### Formatting

- C#
  - `dotnet tool install -g csharpier`
  - install csharpier vscode extension
  - max_line_length is set to 120 in .editorconfig
- Python
  - `pip install ruff`
  - install ruff vscode extension
- JS/TS
  - Prettier
```
