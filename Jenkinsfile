pipeline {
  agent {
    kubernetes {
      label 'python'
      yaml """
apiVersion: v1
kind: Pod
metadata:
  name: python
  labels:
    app: python
spec:
  containers:
  - name: python
    image: fabiocuri/python-walkway:latest
    command: ["cat"]
    tty: true
"""
    }
  }
  stages {
    stage('retrieve-bigquery-data') {
      steps {
        container('python') {
          sh 'python3 src/retrieve_bigquery_data.py'
        }
      }
    }
  }
}