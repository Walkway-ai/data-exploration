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
    image: fabiocuri/python-walkway:latest
    command:
    - cat
    tty: true
"""
        }
    }
    parameters {
        string(name: 'product_id', defaultValue: '9866P79', description: 'The ID of the product')
        choice(name: 'city', choices: ['same', 'different'], description: 'The name of the city')
        choice(name: 'supplier_code', choices: ['same', 'different'], description: 'The supplier code')
    }
    stages {
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
        stage('generate-product-similarity') { 
            steps {
                container('python') {
                    sh 'python3 src/generate_similarity_product.py'
                }
            }
        }
        stage('experiment-product-similarity') { 
            steps {
                container('python') {
                    sh """
                    python3 src/experiment_product_similarity.py \
                        -product_id ${params.product_id} \
                        -city_name ${params.city} \
                        -supplier_code ${params.supplier_code}
                    """
                }
            }
        }
    }
}
