pipeline {
    agent any

    triggers {
        // Poll GitHub every 2 minutes
        pollSCM('H/2 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'master', url: 'https://github.com/jre16/GitHub-Assignment'
            }
        }

        stage('Build in Minikube Docker') {
            steps {
                bat '''
                    REM === Switch Docker to Minikube Docker ===
                    call minikube docker-env --shell=cmd > docker_env.bat
                    call docker_env.bat

                    REM === Build Django image inside Minikube Docker ===
                    docker build -t mydjangoapp:latest .
                '''
            }
        }

        stage('Deploy to Minikube') {
            steps {
                bat '''
                REM Ensure minikube is up and bind kubecontext to THIS session
                minikube status || minikube start --driver=docker --kubernetes-version=v1.34.0
                minikube update-context

                REM Use minikube's kubectl so we don't rely on stale localhost ports
                minikube kubectl -- apply -f deployment.yaml --validate=false
                minikube kubectl -- rollout status deployment/django-deployment --timeout=180s
                '''
            }
        }

    }
}
