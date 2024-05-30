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
- Create a new Cloud of type Kubernetes with Kubernetes URL of the control plane (`kubectl cluster-info`).
- Select "Disable https certificate check".
```