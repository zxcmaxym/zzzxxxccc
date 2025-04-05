#!/bin/bash

# Kill previous port-forward if PID file exists
if [ -f port_forward.pid ]; then
  echo "Killing previous port-forward process..."
  kill $(cat port_forward.pid) 2>/dev/null
  rm port_forward.pid
fi

# Delete and rebuild everything
kubectl delete deployment api
sleep 2
minikube image rm school-api:latest
minikube image rm school-task:latest
../delimg.sh
./create.sh
kubectl apply -f ../k8s/api-deployment.yaml
sleep 20

# Start new port-forward in background and save PID
kubectl port-forward $(kubectl get pods --no-headers -o custom-columns=":metadata.name" | grep '^api-' | head -n 1) 6969:8000 &
echo $! > port_forward.pid

