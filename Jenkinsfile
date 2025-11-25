pipeline {
    agent any

    environment {
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
                    bat '''
                        echo === Checking Minikube status ===
                        minikube status || minikube start --driver=docker
                        
                        echo === Switching to Minikube Docker environment ===
                        @FOR /f "tokens=*" %%i IN ('minikube -p minikube docker-env --shell cmd') DO @%%i
                        docker info | findstr "Server Version"
                    '''
                }
            }
        }

        stage('Build Microservices Images') {
            parallel {
                stage('Build Auth Service') {
                    steps {
                        bat '''
                            @FOR /f "tokens=*" %%i IN ('minikube -p minikube docker-env --shell cmd') DO @%%i
                            echo === Building Auth Service ===
                            docker build -t unipark-auth:latest ./services/auth
                            docker images | findstr unipark-auth
                        '''
                    }
                }
                
                stage('Build Parking Service') {
                    steps {
                        bat '''
                            @FOR /f "tokens=*" %%i IN ('minikube -p minikube docker-env --shell cmd') DO @%%i
                            echo === Building Parking Service ===
                            docker build -t unipark-parking:latest ./services/parking
                            docker images | findstr unipark-parking
                        '''
                    }
                }
                
                stage('Build Reservations Service') {
                    steps {
                        bat '''
                            @FOR /f "tokens=*" %%i IN ('minikube -p minikube docker-env --shell cmd') DO @%%i
                            echo === Building Reservations Service ===
                            docker build -t unipark-reservations:latest ./services/reservations
                            docker images | findstr unipark-reservations
                        '''
                    }
                }
                
                stage('Build Frontend') {
                    steps {
                        bat '''
                            @FOR /f "tokens=*" %%i IN ('minikube -p minikube docker-env --shell cmd') DO @%%i
                            echo === Building Django Frontend ===
                            docker build -t unipark-frontend:latest -f services/frontend/Dockerfile .
                            docker images | findstr unipark-frontend
                        '''
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                bat '''
                    echo === Updating kubectl context ===
                    minikube update-context
                    
                    echo === Applying Kubernetes manifests ===
                    kubectl apply -f k8s/microservices.yaml
                    
                    echo === Waiting for database deployments ===
                    kubectl rollout status deployment/postgres-auth --timeout=180s
                    if errorlevel 1 echo Warning: postgres-auth deployment timeout
                    
                    kubectl rollout status deployment/postgres-parking --timeout=180s
                    if errorlevel 1 echo Warning: postgres-parking deployment timeout
                    
                    kubectl rollout status deployment/postgres-reservations --timeout=180s
                    if errorlevel 1 echo Warning: postgres-reservations deployment timeout
                    
                    kubectl rollout status deployment/postgres-frontend --timeout=180s
                    if errorlevel 1 echo Warning: postgres-frontend deployment timeout
                    
                    echo === Waiting for microservices deployments ===
                    kubectl rollout status deployment/auth-service --timeout=180s
                    if errorlevel 1 echo Warning: auth-service deployment timeout
                    
                    kubectl rollout status deployment/parking-service --timeout=180s
                    if errorlevel 1 echo Warning: parking-service deployment timeout
                    
                    kubectl rollout status deployment/reservations-service --timeout=180s
                    if errorlevel 1 echo Warning: reservations-service deployment timeout
                    
                    kubectl rollout status deployment/unipark-frontend --timeout=180s
                    if errorlevel 1 echo Warning: unipark-frontend deployment timeout
                    
                    echo === Deployment Status ===
                    kubectl get pods
                    kubectl get svc
                '''
            }
        }

        stage('Run Migrations') {
            steps {
                script {
                    bat '''
                        echo === Running Django migrations ===
                        kubectl get pods -l app=unipark-frontend -o jsonpath="{.items[0].metadata.name}" > pod_name.txt
                        set /p POD_NAME=<pod_name.txt
                        echo Running migrations in pod: %POD_NAME%
                        kubectl exec %POD_NAME% -- python manage.py migrate --noinput || echo Migration already ran during startup
                        del pod_name.txt
                    '''
                }
            }
        }

        stage('Get Service URL') {
            steps {
                bat '''
                    echo === Application URLs ===
                    FOR /F "tokens=*" %%i IN ('minikube ip') DO SET MINIKUBE_IP=%%i
                    FOR /F "tokens=*" %%p IN ('kubectl get svc unipark-frontend -o jsonpath="{.spec.ports[0].nodePort}"') DO SET NODEPORT=%%p
                    echo.
                    echo ========================================
                    echo   UNIPARK Application Deployed!
                    echo ========================================
                    echo   Frontend: http://%%i:%%p
                    echo ========================================
                    echo.
                '''
            }
        }
    }

    post {
        success {
            echo '=== DEPLOYMENT SUCCESSFUL ==='
            echo 'Access the application:'
            echo '  Run: minikube service unipark-frontend'
            echo '  Dashboard: kubectl get pods,svc'
        }
        failure {
            echo '=== DEPLOYMENT FAILED ==='
            echo 'Check logs with:'
            echo '  kubectl get pods'
            echo '  kubectl logs -l app=unipark-frontend'
            echo '  kubectl describe pod <pod-name>'
        }
        always {
            bat '''
                echo === Final Status ===
                kubectl get pods
                kubectl get svc
            '''
        }
    }
}
