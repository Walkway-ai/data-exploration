#!/bin/bash

set -e

sudo apt-get update

echo "------------------------------INSTALLING DOCKER------------------------------"
echo "-----------------------------------------------------------------------------"
sudo apt install docker.io -y
sudo systemctl start docker
sudo usermod -aG docker $USER

echo "------------------------------INSTALLING KUBECTL-----------------------------"
echo "-----------------------------------------------------------------------------"
sudo apt-get install kubectl -y

echo "-------------------------------INSTALLING MINIKUBE-------------------------------"
echo "-----------------------------------------------------------------------------"
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube /usr/local/bin/

echo "----------------------SETTING UP KUBERNETES CLUSTER--------------------------"
echo "-----------------------------------------------------------------------------"
minikube start

#admin/[kubectl exec -it svc/jenkins bash][cat /run/secrets/additional/chart-admin-password]
echo "----------------------------INSTALLING JENKINS-------------------------------"
echo "--------------------------https://localhost:8080-----------------------------"
kubectl create namespace jenkins
sudo apt-get install kubectx
kubens jenkins
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
helm repo add jenkins https://charts.jenkins.io
helm repo update
helm install jenkins jenkins/jenkins --set controller.resources.requests.memory=8Gi --set controller.resources.limits.memory=12Gi
kubectl apply -f kubernetes/jenkins-token.yaml
echo "------------------------------BEGINNING TOKEN--------------------------------"
kubectl describe secret $(kubectl describe serviceaccount jenkins | grep token | awk '{print $2}')
echo "---------------------------------END TOKEN-----------------------------------"
kubectl create rolebinding jenkins-admin-binding --clusterrole=admin --serviceaccount=jenkins:jenkins

echo "----------------------------INSTALLING MONGODB-------------------------------"
echo "--------------------------https://localhost:27017----------------------------"
echo "----------------------http://${CLUSTER_NODE_ID}:27017------------------------"
kubectl apply -f kubernetes/walkwayai-configmap.yaml
kubectl apply -f kubernetes/walkwayai-secret.yaml
kubectl apply -f kubernetes/mongodb.yaml
sleep 20
export TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
envsubst < infra-config.yaml > infra-config-pipeline.yaml
git add .
git commit -m "new config"
git push

#admin/pass
echo "-------------------------INSTALLING MONGO EXPRESS----------------------------"
echo "--------------------------https://localhost:8081-----------------------------"
kubectl apply -f kubernetes/mongodb-express.yaml

echo "-----------------------------EXPOSING PORTS---------------------------------"
echo "-----------------------------------------------------------------------------"
sleep 300
export JENKINS_POD=$(kubectl get pods -l app.kubernetes.io/name=jenkins -o jsonpath='{.items[0].metadata.name}')
export MONGODB_POD=$(kubectl get pods -l app=mongodb -o jsonpath='{.items[0].metadata.name}')
export MONGO_EXPRESS_POD=$(kubectl get pods -l app=mongo-express -o jsonpath='{.items[0].metadata.name}')
{
  kill -9 $(lsof -t -i:8080) || true
  kill -9 $(lsof -t -i:27017) || true
  kill -9 $(lsof -t -i:8081) || true
} &>/dev/null
kubectl port-forward $JENKINS_POD 8080:8080 &
kubectl port-forward $MONGODB_POD 27017:27017 &
kubectl port-forward $MONGO_EXPRESS_POD 8081:8081 &