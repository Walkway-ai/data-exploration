pipeline {
  agent {
    kubernetes {
      yaml '''
        apiVersion: v1
        kind: Pod
        spec:
          containers:
          - name: python
            image: python:3.10.12
            command: ["cat"]
            args: []
            tty: true
      '''
    }
  }
  stages {
    stage('install-requirements') {
      steps {
        container('python') {
          sh 'mkdir tmp reports'
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
    /* 
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
    stage('send-data-mongodb') {
      steps {
        container('python') {
          sh 'python3 src/send_data_mongodb.py'
        }
      }
    }
    stage('find-similarity-product') {
      steps {
        container('python') {
          sh 'python3 src/find_similarity_product.py'
        }
      }
    }
    */
  }
}