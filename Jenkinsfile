pipeline {
    agent any
    stages {
        stage('retrieve-bigquery-data') {
            steps {
                script {
                    sh 'kubectl exec -it $(kubectl get pod -l app=python -o jsonpath="{.items[0].metadata.name}") -- python3 src/retrieve_bigquery_data.py'
                }
            }
        }
        stage('generate-product-data') {
            steps {
                script {
                    sh 'kubectl exec -it $(kubectl get pod -l app=python -o jsonpath="{.items[0].metadata.name}") -- python3 src/generate_product_data.py'
                }
            }
        }
        stage('categorize-tabular-data') {
            steps {
                script {
                    sh 'kubectl exec -it $(kubectl get pod -l app=python -o jsonpath="{.items[0].metadata.name}") -- python3 src/categorize_tabular_data.py'
                }
            }
        }
        stage('language-detection') { 
            steps {
                script {
                    sh 'kubectl exec -it $(kubectl get pod -l app=python -o jsonpath="{.items[0].metadata.name}") -- python3 src/language_detection.py'
                }
            }
        }
        stage('text-summarization') { 
            steps {
                script {
                    sh 'kubectl exec -it $(kubectl get pod -l app=python -o jsonpath="{.items[0].metadata.name}") -- python3 src/text_summarization.py'
                }
            }
        }
        stage('create-embeddings') { 
            steps {
                script {
                    sh 'kubectl exec -it $(kubectl get pod -l app=python -o jsonpath="{.items[0].metadata.name}") -- python3 src/embed_textual_data.py'
                }
            }
        }
        stage('create-final-embeddings') { 
            steps {
                script {
                    sh 'kubectl exec -it $(kubectl get pod -l app=python -o jsonpath="{.items[0].metadata.name}") -- python3 src/generate_final_embeddings.py'
                }
            }
        }
        stage('create-final-embeddings') { 
            steps {
                script {
                    sh 'echo test'
                }
            }
        }
    }
}