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
        booleanParam(name: 'OVERWRITE_RETRIEVE_BIGQUERY_DATA', defaultValue: false, description: 'Overwrite data for retrieve-bigquery-data stage')
        booleanParam(name: 'OVERWRITE_GENERATE_PRODUCT_DATA', defaultValue: false, description: 'Overwrite data for generate-product-data stage')
        booleanParam(name: 'OVERWRITE_LANGUAGE_DETECTION', defaultValue: false, description: 'Overwrite data for language-detection stage')
        booleanParam(name: 'OVERWRITE_TEXT_SUMMARIZATION', defaultValue: false, description: 'Overwrite data for text-summarization stage')
        booleanParam(name: 'OVERWRITE_LANDMARK_DETECTION', defaultValue: false, description: 'Overwrite data for landmark-detection stage')
        booleanParam(name: 'OVERWRITE_PRICE_CATEGORIES', defaultValue: false, description: 'Overwrite data for landmark-detection stage')
        booleanParam(name: 'OVERWRITE_SUBCATEGORIES_ANNOTATION', defaultValue: false, description: 'Overwrite annotation of subcategories with OpenAI')
        booleanParam(name: 'OVERWRITE_EMBED_TEXTUAL_DATA', defaultValue: false, description: 'Overwrite data for embed-textual-data stage')
        booleanParam(name: 'OVERWRITE_GENERATE_MODEL_EMBEDDINGS', defaultValue: false, description: 'Overwrite data for generate-model-embeddings stage')
        booleanParam(name: 'OVERWRITE_GENERATE_PRODUCT_SIMILARITY', defaultValue: false, description: 'Overwrite data for generate-product-similarity stage')
    }
    stages {
        stage('retrieve-bigquery-data') {
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_RETRIEVE_BIGQUERY_DATA ? '--overwrite' : ''
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
                            sh("python3 src/retrieve_bigquery_data.py ${overwriteArg}")
                        }
                    }
                }
            }
        }
        stage('generate-product-data') {
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_GENERATE_PRODUCT_DATA ? '--overwrite' : ''
                        sh("python3 src/generate_product_data.py ${overwriteArg}")
                    }
                }
            }
        }
        stage('language-detection') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_LANGUAGE_DETECTION ? '--overwrite' : ''
                        sh("python3 src/language_detection.py ${overwriteArg}")
                    }
                }
            }
        }
        stage('text-summarization') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_TEXT_SUMMARIZATION ? '--overwrite' : ''
                        sh("mkdir tmp")
                        sh("python3 src/text_summarization.py ${overwriteArg} --summarization_model 'facebook/bart-large-cnn'")
                    }
                }
            }
        }
        stage('landmark-detection') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_LANDMARK_DETECTION ? '--overwrite' : ''
                        sh("python3 src/landmark_detection.py ${overwriteArg}")
                    }
                }
            }
        }
        stage('generate-price-categories') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_PRICE_CATEGORIES ? '--overwrite' : ''
                        sh("python3 src/generate_price_categories.py ${overwriteArg}")
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
                        sh("python3 src/generate_model_embeddings.py ${overwriteArg} --embedding_model 'thenlper/gte-large'")
                        sh("python3 src/generate_model_embeddings.py ${overwriteArg} --embedding_model 'jinaai/jina-embeddings-v2-base-en'")
                        sh("python3 src/generate_mean_embeddings.py ${overwriteArg} --embedding_models 'thenlper/gte-large,jinaai/jina-embeddings-v2-base-en'")
                    }
                }
            }
        }
        stage('generate-product-similarity') { 
            steps {
                container('python') {
                    script {
                        def overwriteArg = params.OVERWRITE_GENERATE_PRODUCT_SIMILARITY ? '--overwrite' : ''
                        sh("python3 src/generate_product_similarity.py ${overwriteArg} --embedding_model 'thenlper/gte-large'")
                        sh("python3 src/generate_product_similarity.py ${overwriteArg} --embedding_model 'jinaai/jina-embeddings-v2-base-en'")
                        sh("python3 src/generate_product_similarity.py ${overwriteArg} --embedding_model 'mean/mean'")
                    }
                }
            }
        }
    }
}
