pipeline {
    agent {
        kubernetes {
            label 'python-agent'
            defaultContainer 'python'
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    some-label: python
spec:
  containers:
  - name: python
    image: python:3.9
    command:
    - cat
    tty: true
"""
        }
    }
    stages {
        stage('Install Dependencies') {
            steps {
                container('python') {
                    sh 'pip install -r requirements.txt'
                }
            }
        }
        stage('retrieve-bigquery-data') {
            steps {
                container('python') {
                    sh 'python3 src/retrieve_bigquery_data.py'
                }
            }
        }
        stage('generate-product-data') {
            steps {
                container('python') {
                    sh 'python3 src/generate_product_data.py'
                }
            }
        }
        stage('categorize-tabular-data') {
            steps {
                container('python') {
                    sh 'python3 src/categorize_tabular_data.py'
                }
            }
        }
        stage('language-detection') { 
            steps {
                container('python') {
                    sh 'python3 src/language_detection.py'
                }
            }
        }
        stage('text-summarization') { 
            steps {
                container('python') {
                    sh 'python3 src/text_summarization.py'
                }
            }
        }
        stage('create-embeddings') { 
            steps {
                container('python') {
                    sh 'python3 src/embed_textual_data.py'
                }
            }
        }
        stage('create-final-embeddings') { 
            steps {
                container('python') {
                    sh 'python3 src/generate_final_embeddings.py'
                }
            }
        }
        stage('product-similarity') { 
            steps {
                container('python') {
                    sh 'echo test'
                }
            }
        }
    }
}
