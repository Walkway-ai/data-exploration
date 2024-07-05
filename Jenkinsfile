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
    image: walkwayai/python:2.0
    command:
    - cat
    tty: true
"""
        }
    }
    parameters {
        choice(name: 'embedding_fields', choices: ['title_inclexcl_tgdescription', 'description_title', 'description_inclexcl'], description: 'Fields for the embedding model.')
    }
    stages {
        stage('retrieve-bigquery-data') {
            steps {
                container('python') {
                    script {
                        withCredentials([file(credentialsId: 'gcp_service_account_json', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                            sh("apt-get update && apt-get install -y git curl")
                            sh("curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-367.0.0-linux-x86_64.tar.gz")
                            sh("tar -xf google-cloud-sdk-367.0.0-linux-x86_64.tar.gz")
                            sh("yes | ./google-cloud-sdk/install.sh")
                            sh("yes | ./google-cloud-sdk/bin/gcloud components install gke-gcloud-auth-plugin")
                            sh("rm google-cloud-sdk-367.0.0-linux-x86_64.tar.gz")
                            sh("apt-get clean && rm -rf /var/lib/apt/lists/*")
                            sh("export GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS")
                            sh("./google-cloud-sdk/bin/gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS")
                            sh("python3 src/retrieve_bigquery_data.py --overwrite")
                        }
                    }
                }
            }
        }
        stage('generate-product-data') {
            steps {
                container('python') {
                    script {
                        sh("python3 src/generate_product_data.py --overwrite")
                    }
                }
            }
        }
        stage('language-detection') { 
            steps {
                container('python') {
                    script {
                        sh("python3 src/language_detection.py --overwrite")
                    }
                }
            }
        }
        stage('text-summarization') { 
            steps {
                container('python') {
                    script {
                        sh("mkdir tmp")
                        sh("python3 src/text_summarization.py --overwrite --summarization_model 'facebook/bart-large-cnn'")
                    }
                }
            }
        }
        stage('landmark-detection') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_LANDMARK_DETECTION ? '--overwrite' : ''
                        sh("python3 src/landmark_detection.py --overwrite")
                    }
                }
            }
        }
        stage('generate-price-table') { 
            steps {
                container('python') {
                    script {
                        sh("python3 src/generate_price_table.py --overwrite")
                    }
                }
            }
        }
        stage('generate-reviews-table') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_PRICE_CATEGORIES ? '--overwrite' : ''
                        sh("python3 src/generate_reviews_table.py --overwrite")
                    }
                }
            }
        }
        stage('subcategories-annotation') { 
            steps {
                container('python') {
                    script {
                        withCredentials([string(credentialsId: 'OPENAI_API_KEY', variable: 'OPENAI_API_KEY')]) {
                            def overwriteArg = params.OVERWRITE_SUBCATEGORIES_ANNOTATION ? '--overwrite' : ''
                            sh("python3 src/annotate_subcategories_gpt.py ${overwriteArg} --model_name 'gpt-4o' --apikey ${OPENAI_API_KEY}")
                            sh("python3 src/map_gpt_categories_to_taxonomy.py ${overwriteArg} --model_name 'gpt-4o' --apikey ${OPENAI_API_KEY}")
                            sh("python3 src/extend_taxonomy_db.py ${overwriteArg}")
                        }
                    }
                }
            }
        }
        stage('embed-textual-data') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_EMBED_TEXTUAL_DATA ? '--overwrite' : ''
                        sh("python3 src/embed_textual_data.py ${overwriteArg} --embedding_model 'thenlper/gte-large'")
                        sh("python3 src/embed_textual_data.py ${overwriteArg} --embedding_model 'jinaai/jina-embeddings-v2-base-en'")
                    }
                }
            }
        }
        stage('generate-model-embeddings') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_GENERATE_MODEL_EMBEDDINGS ? '--overwrite' : ''
                        sh("python3 src/generate_model_embeddings.py ${overwriteArg} --embedding_model 'thenlper/gte-large' --embedding_fields ${params.embedding_fields}")
                        sh("python3 src/generate_model_embeddings.py ${overwriteArg} --embedding_model 'jinaai/jina-embeddings-v2-base-en' --embedding_fields ${params.embedding_fields}")
                        sh("python3 src/generate_mean_embeddings.py ${overwriteArg} --embedding_models 'thenlper/gte-large,jinaai/jina-embeddings-v2-base-en' --embedding_fields ${params.embedding_fields}")
                    }
                }
            }
        }
        stage('generate-product-similarity') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_GENERATE_PRODUCT_SIMILARITY ? '--overwrite' : ''
                        sh("python3 src/generate_product_similarity.py ${overwriteArg} --embedding_model 'mean/mean'")
                    }
                }
            }
        }
    }
}
