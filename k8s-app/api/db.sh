#!/bin/bash
kubectl delete deployment postgres
kubectl delete pvc postgres-pvc
kubectl delete service postgres
kubectl apply -f ../k8s/postgres-deployment.yaml

