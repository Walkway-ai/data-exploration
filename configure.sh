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

# Install MongoDB
helm install mongodb bitnami/mongodb

# Install Mongo Express
helm install mongo-express bitnami/mongodb
