#!/bin/bash

# Build the Docker image
echo "Building frontend Docker image..."
docker build -t school-frontend:latest .

# Apply Kubernetes deployment
echo "Applying Kubernetes deployment..."
kubectl apply -f ../k8s/frontend-deployment.yaml

echo "Frontend deployment complete!"
echo "Use 'kubectl get services' to check the service status." 