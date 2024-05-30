#!/bin/bash

set -e

gcloud auth login
gcloud config set project "ww-da-ingestion"
gcloud container clusters create walkway-cluster --num-nodes=1 --zone=us-central1-c
gcloud container clusters get-credentials walkway-cluster --zone us-central1-c

# Install Jenkins
helm repo add jenkins https://charts.jenkins.io
helm install jenkins jenkins/jenkins --namespace jenkins --set service.type=LoadBalancer

# Install MongoDB
helm install mongodb bitnami/mongodb --namespace mongodb

# Install Mongo Express
helm install mongo-express bitnami/mongodb --namespace mongodb
