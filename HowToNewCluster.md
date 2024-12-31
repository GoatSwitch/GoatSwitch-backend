# New Kubernetes GS Cluster

## Create Cluster

First set relevant variables
(also az login?)

```
RESGRP="GoatSwitchAI_Azuresponsored"
CLNAME=GoatSwitchCluster2
ACRNAME=goatswitch
```

Create the kubernetes cluster

```
az aks create \
    --resource-group $RESGRP \
    --name $CLNAME \
    --node-count 1 \
    --network-plugin azure \ #  This enables windows containers
    --vm-set-type VirtualMachineScaleSets \
    --generate-ssh-keys \
    --node-vm-size Standard_D2_v5 \  # Cheaper vms than default
    --node-osdisk-type Managed \
    --node-osdisk-size 64 \  # less storage than default for cost
    --attach-acr $ACRNAME # attach container registry
```

(takes a few minutes)

### Verify it went well

```
az aks get-credentials --resource-group $RESGRP --name $CLNAME
kubectl get nodes
```

### Add nodepools

Add a linux and a windows nodepool.

```
az aks nodepool add \
    --name winnp \
    --resource-group $RESGRP \
    --cluster-name $CLNAME \
    --os-type Windows \
    --node-vm-size Standard_D2_v5 \  # Cheap vms
    --node-osdisk-type Managed \
    --node-osdisk-size 64 \  # Cheap storage
    --priority Spot \  # Cheap spot instances
    --aks-custom-headers WindowsContainerRuntime=containerd \
    --node-count 1

az aks nodepool add \
    --name spotpool \
    --cluster-name $CLNAME \
    --resource-group $RESGRP \
    -s Standard_D2_v5 \
    --node-osdisk-type Managed \
    --node-osdisk-size 64 \
    --priority Spot \
    --mode User \
    --os-sku Ubuntu \
    --node-count 1 \
    --spot-max-price 0.02 \
    --eviction-policy deallocate  \
```

(takes a few minutes)

### Fix systempool

Forgot to change os disk max pods at start, heres how to change nodepools after creating:

```
az aks nodepool add \
    --name systempool \
    --cluster-name $CLNAME \
    --resource-group $RESGRP \
    -s Standard_D2_v5 \
    --node-osdisk-type Managed \
    --node-osdisk-size 64 \
    --priority Regular \
    --mode System \
    --os-sku Ubuntu \
    --node-count 1 \
    --max-pods 110
```

### add taint to distinguish windows and linux nodes

```
az aks nodepool update \
    --name winnp \
    --cluster-name $CLNAME \
    --resource-group $RESGRP \
    --node-taints os=windows:NoSchedule \
az aks nodepool update \
    --name spotpool\
    --cluster-name $CLNAME \
    --resource-group $RESGRP \
    --node-taints os=linux:NoSchedule
```

## Install stuff

Install dapr

```
DO NOT USE dapr init -k
```

Install via helm

```
helm repo add dapr https://dapr.github.io/helm-charts/
helm repo update
helm install dapr dapr/dapr --namespace dapr-system --create-namespace --values helm-values/dapr-values.yaml --wait
```

### Add kubernetes-dashboard repository

```
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
# Deploy a Helm Release named "kubernetes-dashboard" using the kubernetes-dashboard chart
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard

# configure roles using azure GUI -> GoatSwitchCluster2 -> Settings -> Cluster Configuration -> Authentication and Authorization
az aks update -g MyResourceGroup -n myManagedCluster --enable-aad --aad-admin-group-object-ids <id-1>,<id-2> [--aad-tenant-id <id>]

# add GS-Cluster-Admin role as cluster admin role
```

(brew install Azure/kubelogin/kubelogin
kubelogin convert-kubeconfig -l azurecli)

Admin user for kubernetes dashboard login

```
kubectl apply -f dashboard-adminuser.yaml

# get token for login
kubectl -n kubernetes-dashboard create token admin-user

# forward port so dashbaord is exposed on https://localhost:8443/#/
kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443
```

http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard-kong-proxy:443/proxy/#/login

Enable blob storage driver, not sure exactly if this is necessary

```
az aks update --enable-blob-driver -n $CLNAME -g $RESGRP
```
