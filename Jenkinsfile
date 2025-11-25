pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'docker.io'
        IMAGE_NAME = 'unipark'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                echo '=== Checking out code from GitHub ==='
                checkout scm
            }
        }

        stage('Setup Minikube Environment') {
            steps {
                script {
                    sh '''
                        echo "=== Checking Minikube status ==="
                        minikube status || minikube start --driver=docker
                        
                        echo "=== Switching to Minikube Docker environment ==="
                        eval $(minikube docker-env)
                        docker info | grep "Server Version"
                    '''
                }
            }
        }

        stage('Build Microservices Images') {
            parallel {
                stage('Build Auth Service') {
                    steps {
                        sh '''
                            eval $(minikube docker-env)
                            echo "=== Building Auth Service ==="
                            docker build -t unipark-auth:latest ./services/auth
                            docker images | grep unipark-auth
                        '''
                    }
                }
                
                stage('Build Parking Service') {
                    steps {
                        sh '''
                            eval $(minikube docker-env)
                            echo "=== Building Parking Service ==="
                            docker build -t unipark-parking:latest ./services/parking
                            docker images | grep unipark-parking
                        '''
                    }
                }
                
                stage('Build Reservations Service') {
                    steps {
                        sh '''
                            eval $(minikube docker-env)
                            echo "=== Building Reservations Service ==="
                            docker build -t unipark-reservations:latest ./services/reservations
                            docker images | grep unipark-reservations
                        '''
                    }
                }
                
                stage('Build Frontend') {
                    steps {
                        sh '''
                            eval $(minikube docker-env)
                            echo "=== Building Django Frontend ==="
                            docker build -t unipark-frontend:latest -f services/frontend/Dockerfile .
                            docker images | grep unipark-frontend
                        '''
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                    echo "=== Updating kubectl context ==="
                    minikube update-context
                    
                    echo "=== Applying Kubernetes manifests ==="
                    kubectl apply -f k8s/microservices.yaml
                    
                    echo "=== Waiting for database deployments ==="
                    kubectl rollout status deployment/postgres-auth --timeout=180s || true
                    kubectl rollout status deployment/postgres-parking --timeout=180s || true
                    kubectl rollout status deployment/postgres-reservations --timeout=180s || true
                    kubectl rollout status deployment/postgres-frontend --timeout=180s || true
                    
                    echo "=== Waiting for microservices deployments ==="
                    kubectl rollout status deployment/auth-service --timeout=180s || true
                    kubectl rollout status deployment/parking-service --timeout=180s || true
                    kubectl rollout status deployment/reservations-service --timeout=180s || true
                    kubectl rollout status deployment/unipark-frontend --timeout=180s || true
                    
                    echo "=== Deployment Status ==="
                    kubectl get pods
                    kubectl get svc
                '''
            }
        }

        stage('Run Migrations') {
            steps {
                sh '''
                    echo "=== Running Django migrations ==="
                    POD_NAME=$(kubectl get pods -l app=unipark-frontend -o jsonpath="{.items[0].metadata.name}")
                    echo "Running migrations in pod: $POD_NAME"
                    kubectl exec $POD_NAME -- python manage.py migrate --noinput || echo "Migration already ran during startup"
                '''
            }
        }

        stage('Get Service URL') {
            steps {
                sh '''
                    echo "=== Application URLs ==="
                    echo "Frontend: http://$(minikube ip):30080"
                    minikube service unipark-frontend --url || true
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Deployment successful!'
            echo 'Access the application:'
            echo '  Frontend: minikube service unipark-frontend'
            echo '  Dashboard: kubectl get pods,svc'
        }
        failure {
            echo '❌ Deployment failed!'
            echo 'Check logs with:'
            echo '  kubectl get pods'
            echo '  kubectl logs -l app=unipark-frontend'
            echo '  kubectl describe pod <pod-name>'
        }
        always {
            echo '=== Final Status ==='
            sh 'kubectl get pods || true'
            sh 'kubectl get svc || true'
        }
    }
}
