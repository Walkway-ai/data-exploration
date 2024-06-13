pipeline {
    agent {
        kubernetes {
            label 'python'
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
    image: walkwayai/python:latest
    command:
    - cat
    tty: true
"""
        }
    }
    environment {
        GOOGLE_APPLICATION_CREDENTIALS = credentials('google-service-account-key')
    }
    stages {
        stage('retrieve-bigquery-data') {
            steps {
                container('python') {
                    sh '''
                    export GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS}"
                    python3 src/retrieve_bigquery_data.py --overwrite
                    '''
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
                    sh 'mkdir tmp'
                    sh 'python3 src/text_summarization.py'
                }
            }
        }
        stage('embed-textual-data') { 
            steps {
                container('python') {
                    sh 'python3 src/embed_textual_data.py'
                }
            }
        }
        stage('generate-final-embeddings') { 
            steps {
                container('python') {
                    sh 'python3 src/generate_final_embeddings.py'
                }
            }
        }
        stage('generate-product-similarity') { 
            steps {
                container('python') {
                    sh 'python3 src/generate_product_similarity.py'
                }
            }
        }
    }
}
