# Jenkins Setup for UNIPARK 2.0 Microservices

## Prerequisites

1. Docker Desktop running
2. Minikube installed and accessible
3. kubectl configured

## Step 1: Start Jenkins

```bash
# Start Jenkins with Docker and Minikube access
docker-compose -f docker-compose-jenkins.yml up -d

# Wait for Jenkins to start (30-60 seconds)
docker logs -f jenkins_jenkins_1
```

## Step 2: Install Required Tools in Jenkins Container

```bash
# Access Jenkins container
docker exec -it -u root jenkins_jenkins_1 bash

# Install Docker CLI
apt-get update
apt-get install -y docker.io

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
mv kubectl /usr/local/bin/

# Install Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
install minikube-linux-amd64 /usr/local/bin/minikube

# Verify installations
docker --version
kubectl version --client
minikube version

# Exit container
exit
```

## Step 3: Configure Jenkins

1. **Get Initial Admin Password:**
   ```bash
   docker exec jenkins_jenkins_1 cat /var/jenkins_home/secrets/initialAdminPassword
   ```

2. **Access Jenkins:**
   - Open browser: http://localhost:8080
   - Paste the admin password
   - Install suggested plugins

3. **Create Admin User:**
   - Username: admin
   - Password: (your choice)
   - Email: your-email@example.com

## Step 4: Install Required Jenkins Plugins

Go to **Manage Jenkins → Manage Plugins → Available**

Install these plugins:
- ✅ Git plugin
- ✅ Pipeline
- ✅ Docker Pipeline
- ✅ Kubernetes CLI Plugin
- ✅ GitHub plugin

Restart Jenkins after installation.

## Step 5: Create Pipeline Job

1. **New Item:**
   - Click "New Item"
   - Enter name: `UNIPARK-Microservices`
   - Select "Pipeline"
   - Click OK

2. **Configure Pipeline:**
   - **General:**
     - ✅ GitHub project
     - Project URL: `https://github.com/jre16/uni_park`
   
   - **Build Triggers:**
     - ✅ Poll SCM
     - Schedule: `H/5 * * * *` (every 5 minutes)
   
   - **Pipeline:**
     - Definition: `Pipeline script from SCM`
     - SCM: `Git`
     - Repository URL: `https://github.com/jre16/uni_park`
     - Branch: `*/main`
     - Script Path: `Jenkinsfile`

3. **Save**

## Step 6: Configure Minikube Access in Jenkins

```bash
# Start Minikube (if not running)
minikube start --driver=docker

# Copy Minikube config to Jenkins
docker cp ~/.minikube jenkins_jenkins_1:/root/.minikube
docker cp ~/.kube jenkins_jenkins_1:/root/.kube

# Set permissions in Jenkins container
docker exec -u root jenkins_jenkins_1 chown -R jenkins:jenkins /root/.minikube /root/.kube
```

## Step 7: Run Pipeline

1. Go to your pipeline job
2. Click "Build Now"
3. Watch the build progress in "Console Output"

## Troubleshooting

### Docker not found
```bash
docker exec -u root jenkins_jenkins_1 bash
apt-get update && apt-get install -y docker.io
chmod 666 /var/run/docker.sock
```

### Minikube not accessible
```bash
# In Jenkins container
docker exec -it jenkins_jenkins_1 bash
minikube status
eval $(minikube docker-env)
```

### kubectl not working
```bash
docker exec jenkins_jenkins_1 kubectl get nodes
# If fails, copy kubeconfig again
```

## Expected Pipeline Flow

1. ✅ Checkout code from GitHub
2. ✅ Setup Minikube environment
3. ✅ Build 4 Docker images in parallel:
   - unipark-auth:latest
   - unipark-parking:latest
   - unipark-reservations:latest
   - unipark-frontend:latest
4. ✅ Deploy to Kubernetes (apply microservices.yaml)
5. ✅ Wait for all deployments to be ready
6. ✅ Run Django migrations
7. ✅ Display service URLs

## Monitoring

```bash
# View Jenkins logs
docker logs -f jenkins_jenkins_1

# View Kubernetes pods
kubectl get pods

# View services
kubectl get svc

# Access application
minikube service unipark-frontend
```

## Stopping Jenkins

```bash
# Stop Jenkins
docker-compose -f docker-compose-jenkins.yml down

# Stop and remove volumes (WARNING: Deletes all data)
docker-compose -f docker-compose-jenkins.yml down -v
```

## Notes

- Jenkins runs on port 8080
- Application runs on Minikube NodePort 30080
- All builds use Minikube's Docker daemon
- Images are built inside Minikube cluster
- No need to push to Docker Hub (uses local images)
