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
                    sh 'python3 src/generate_product_data.py --overwrite'
                }
            }
        }
        stage('categorize-tabular-data') {
            steps {
                container('python') {
                    sh 'python3 src/categorize_tabular_data.py --overwrite'
                }
            }
        }
        stage('language-detection') { 
            steps {
                container('python') {
                    sh 'python3 src/language_detection.py --overwrite'
                }
            }
        }
        stage('text-summarization') { 
            steps {
                container('python') {
                    sh 'mkdir tmp'
                    sh 'python3 src/text_summarization.py --overwrite --summarization_model "facebook/bart-large-cnn"'
                }
            }
        }
        stage('landmark-detection') { 
            steps {
                container('python') {
                    script {
                        withCredentials([string(credentialsId: 'OPENAI_API_KEY', variable: 'OPENAI_API_KEY')]) {
                            sh """
                            python3 src/landmark_detection.py --overwrite 
                            """
                        }
                    }
                }
            }
        }
        stage('embed-textual-data') { 
            steps {
                container('python') {
                    sh 'python3 src/embed_textual_data.py --overwrite --embedding_model "thenlper/gte-large"'
                    // sh 'python3 src/embed_textual_data.py --overwrite --embedding_model "jinaai/jina-embeddings-v2-base-en"'
                }
            }
        }
        stage('generate-model-embeddings') { 
            steps {
                container('python') {
                    sh 'python3 src/generate_model_embeddings.py --overwrite --embedding_model "thenlper/gte-large"'
                    // sh 'python3 src/generate_model_embeddings.py --overwrite --embedding_model "jinaai/jina-embeddings-v2-base-en"'

                }
            }
        }
        stage('generate-mean-embeddings') { 
            steps {
                container('python') {
                    sh 'python3 src/generate_mean_embeddings.py --overwrite --embedding_models "thenlper/gte-large,jinaai/jina-embeddings-v2-base-en"'
                }
            }
        }
        stage('generate-product-similarity') { 
            steps {
                container('python') {
                    sh 'python3 src/generate_product_similarity.py --overwrite --embedding_model "thenlper/gte-large"'
                    // sh 'python3 src/generate_product_similarity.py --overwrite --embedding_model "jinaai/jina-embeddings-v2-base-en"'
                    // sh 'python3 src/generate_product_similarity.py --overwrite --embedding_model "mean/mean"'
                }
            }
        }
    }
}
