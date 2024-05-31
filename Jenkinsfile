pipeline {
  agent any
  stages {
    stage('create-python-env') {
      steps {
        script {
          sh 'kubectl apply -f pod-python.yaml'
        }
      }
    }
    stage('retrieve-bigquery-data') {
      steps {
        script {
          sh 'kubectl exec -it $(kubectl get pod -l app=python -o jsonpath="{.items[0].metadata.name}") -- python3 /path/to/src/retrieve_bigquery_data.py'
        }
      }
    }
  }
}