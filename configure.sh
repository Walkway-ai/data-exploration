#!/bin/bash

set -e

sudo apt-get update

echo "------------------------------INSTALLING DOCKER------------------------------"
echo "-----------------------------------------------------------------------------"
sudo apt install docker.io -y
sudo systemctl start docker
echo "------------------------------INSTALLING KUBECTL-----------------------------"
echo "-----------------------------------------------------------------------------"
sudo apt-get install kubectl -y
echo "-------------------------------INSTALLING KIND-------------------------------"
echo "-----------------------------------------------------------------------------"
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
[ $(uname -m) = aarch64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-arm64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
echo "----------------------SETTING UP KUBERNETES CLUSTER--------------------------"
echo "-----------------------------------------------------------------------------"
ip_addresses=$(hostname -I)
export MY_IP_ADDRESS=$(echo "$ip_addresses" | awk '{print $1}')
kind delete cluster --name kind
envsubst < kubernetes/cluster.yaml | kind create cluster --retain --config=-
kubectl cluster-info --context kind-kind
echo "-------------------------------INSTALLING KUBENS-------------------------------"
echo "-----------------------------------------------------------------------------"
sudo apt-get install kubectx
echo "-------------------------------INSTALLING HELM-------------------------------"
echo "-----------------------------------------------------------------------------"
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
echo "----------------------------INSTALLING JENKINS-------------------------------"
echo "-----------------------------------------------------------------------------"
#admin/[kubectl exec -it svc/jenkins bash][cat /run/secrets/additional/chart-admin-password]
kubectl create namespace jenkins
kubens jenkins
helm repo add jenkins https://charts.jenkins.io
helm repo update
helm install jenkins jenkins/jenkins --set controller.resources.requests.memory=16Gi --set controller.resources.limits.memory=48Gi
kubectl apply -f kubernetes/jenkins-token.yaml
echo "------------------------------BEGINNING TOKEN--------------------------------"
kubectl describe secret $(kubectl describe serviceaccount jenkins | grep token | awk '{print $2}')
echo "---------------------------------END TOKEN-----------------------------------"
kubectl create rolebinding jenkins-admin-binding --clusterrole=admin --serviceaccount=jenkins:jenkins
echo "----------------------------INSTALLING MONGODB-------------------------------"
kubectl apply -f kubernetes/walkwayai-configmap.yaml
kubectl apply -f kubernetes/walkwayai-secret.yaml
kubectl apply -f kubernetes/mongodb.yaml
sleep 20
export CLUSTER_NODE_ID=$(kubectl get node -o wide | awk 'NR==2 {print $6}')
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