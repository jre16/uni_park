pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image in Minikube') {
            steps {
                bat '''
                    @echo off
                    echo === Switching to Minikube Docker environment ===
                    for /f "tokens=*" %%i in ('minikube docker-env --shell cmd') do %%i
                    
                    echo === Building UNIPARK Docker image ===
                    docker build -t unipark:latest .
                    
                    echo === Verifying image ===
                    docker images | findstr unipark
                '''
            }
        }

        stage('Deploy to Minikube') {
            steps {
                bat '''
                    @echo off
                    echo === Ensuring Minikube is running ===
                    minikube status || minikube start --driver=docker
                    
                    echo === Updating kubectl context ===
                    minikube update-context
                    
                    echo === Applying Kubernetes manifests ===
                    kubectl apply -f k8s/deployment.yaml
                    
                    echo === Waiting for deployments ===
                    kubectl rollout status deployment/postgres-deployment --timeout=180s
                    kubectl rollout status deployment/django-deployment --timeout=180s
                    
                    echo === Getting service URL ===
                    minikube service django-service --url
                '''
            }
        }

        stage('Run Migrations') {
            steps {
                bat '''
                    @echo off
                    echo === Running Django migrations ===
                    for /f "tokens=*" %%i in ('kubectl get pods -l app=django-app -o jsonpath="{.items[0].metadata.name}"') do set POD_NAME=%%i
                    kubectl exec %POD_NAME% -- python manage.py migrate --noinput
                '''
            }
        }
    }

    post {
        success {
            echo 'Deployment successful! Access the app using: minikube service django-service'
        }
        failure {
            echo 'Deployment failed. Check logs with: kubectl logs -l app=django-app'
        }
    }
}
