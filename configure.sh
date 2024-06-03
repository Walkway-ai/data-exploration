#!/bin/bash

set -e

# Set up GCP SDK and install dependencies
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-478.0.0-linux-x86_64.tar.gz
tar -xf google-cloud-cli-478.0.0-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh
./google-cloud-sdk/bin/gcloud init
gcloud components install gke-gcloud-auth-plugin

# Create cluster and configure KUBECONFIG
gcloud container clusters create walkway-cluster --num-nodes=3 --zone=us-central1-c
export USE_GKE_GCLOUD_AUTH_PLUGIN=True
gcloud container clusters get-credentials walkway-cluster --zone us-central1-c

# Set up Helm
helm repo add jenkins https://charts.jenkins.io
helm repo add cowboysysop https://cowboysysop.github.io/charts/
helm repo update

# Install Jenkins
helm install jenkins jenkins/jenkins
kubectl expose service jenkins --type=LoadBalancer --name=jenkins-lb
#admin/[kubectl exec -it svc/jenkins bash][cat /run/secrets/additional/chart-admin-password]
#admin/walkway

# Install MongoDB
helm install mongo oci://registry-1.docker.io/bitnamicharts/mongodb --set auth.rootUser=walkway --set auth.rootPassword=walkway
kubectl expose service mongo-mongodb --type=LoadBalancer --name=mongodb-lb

# Install Mongo Express
helm install mongo-express cowboysysop/mongo-express \
  --set mongodbServer=mongodb-lb \
  --set mongodbPort=27017 \
  --set mongodbEnableAdmin=true \
  --set mongodbAdminUsername=walkway \
  --set mongodbAdminPassword=walkway \
  --set basicAuthUsername=admin \
  --set basicAuthPassword=walkway

kubectl expose service mongo-express --type=LoadBalancer --name=mongo-express-lb

export TIMESTAMP=$(date +%s)
export MONGO_DB_EXTERNAL_IP=$(kubectl get service mongodb-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
envsubst < infra-config.yaml > infra-config-pipeline.yaml

# Create Python image
docker build -t fabiocuri/python-walkway:latest .
docker tag fabiocuri/python-walkway:latest fabiocuri/python-walkway:latest
docker push fabiocuri/python-walkway:latest