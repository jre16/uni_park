pipeline {
    agent any

    environment {
        IMAGE_NAME = "unipark:latest"
        K8S_DIR = "k8s"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image for Minikube') {
            steps {
                sh """
                eval \$(minikube docker-env)
                docker build -t $IMAGE_NAME .
                """
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh """
                kubectl apply -f $K8S_DIR
                """
            }
        }

        stage('Run Django Migrations') {
            steps {
                sh """
                POD=\$(kubectl get pods -l app=unipark -o jsonpath="{.items[0].metadata.name}")
                kubectl exec \$POD -- python manage.py migrate --noinput
                """
            }
        }
    }

    post {
        success {
            echo '✅ UniPark deployed successfully!'
        }
        failure {
            echo '❌ Deployment failed — check Jenkins logs.'
        }
    }
}
