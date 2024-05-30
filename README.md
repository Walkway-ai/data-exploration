# Product Similarity

## Stack

Language: Python, Bash, Groovy

CI/CD: Jenkins

Database: MongoDB

Deployment: Kubernetes

## Setup

```bash
bash configure.sh
```

## Jenkins Configuration

```markdown

1. Open Jenkins and navigate to "Build Executor Status" > Main cluster.
2. Set the Number of executors to 0 and create a label (e.g., "kubernetes-cluster"). Select "Only build jobs with labels...".
3. Install the Kubernetes plugin.
4. Create a new Cloud of type Kubernetes. Use the URL obtained from `kubectl cluster-info --context kind-kind`.
   - Add "jenkins" as the namespace.
   - Select "Disable https certificate check".
   - Create a new credential named "k8s-token" as a long text, and paste the TOKEN value.
     TOKEN is result from `kubectl describe secret $(kubectl describe serviceaccount jenkins | grep token | awk '{print $2}')`.
5. Create and run a new pipeline pointing to this project.
6. Install "Stage View" plugin for better visualisation of pipeline.
```