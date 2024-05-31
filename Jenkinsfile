pipeline {
  agent any
  stages {
    stage('retrieve-bigquery-data') {
      steps {
        script {
          sh 'kubectl exec -it $(kubectl get pod -l app=python -o jsonpath="{.items[0].metadata.name}") bash -- python3 src/retrieve_bigquery_data.py'
        }
      }
    }
  }
}