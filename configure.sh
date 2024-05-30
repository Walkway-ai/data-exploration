#!/bin/bash

set -e

# Set up GCP CLI
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-478.0.0-linux-x86_64.tar.gz
tar -xf google-cloud-cli-478.0.0-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh
./google-cloud-sdk/bin/gcloud init

# Install Plugin
gcloud components install gke-gcloud-auth-plugin

# Set local KUBECONFIG
gcloud container clusters create walkway-cluster --num-nodes=1 --zone=us-central1-c
export USE_GKE_GCLOUD_AUTH_PLUGIN=True
gcloud container clusters get-credentials walkway-cluster --zone us-central1-c

kubectl create namespace jenkins
helm repo add jenkins https://charts.jenkins.io
helm repo update

# Install Jenkins
helm install jenkins jenkins/jenkins
kubectl expose service jenkins --type=LoadBalancer --name=jenkins-lb
#http://34.70.65.70:8080/
#admin/[kubectl exec -it svc/jenkins bash][cat /run/secrets/additional/chart-admin-password]
#admin/walkway

# Install MongoDB
kubectl apply -f kubernetes/walkwayai-configmap.yaml
kubectl apply -f kubernetes/walkwayai-secrets.yaml
kubectl apply -f kubernetes/mongodb.yaml
sleep 20
export CLUSTER_NODE_ID=$(kubectl get node -o wide | awk 'NR==2 {print $6}')
export TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
envsubst < infra-config.yaml > infra-config-pipeline.yaml
git add .
git commit -m "new config"
git push

# Install Mongo Express
helm install mongo-express bitnami/mongodb
