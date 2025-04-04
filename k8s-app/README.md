# School Task Management System

This is a Kubernetes-based application for managing school tasks and assignments. The system consists of a PostgreSQL database and a FastAPI server that can create and manage task pods.

## Architecture

The application consists of the following components:

1. **PostgreSQL Database**: Stores student, teacher, task, and result information.
2. **FastAPI Server**: Provides API endpoints for students and teachers to interact with the system.
3. **Task Pods**: Temporary pods created for each homework assignment to validate student submissions.

## API Endpoints

### Student Interface

- **POST /student/validate**: Upload and validate a student task
- **GET /student**: Get information about the student interface
- **GET /student/task/result/{task}/{name}**: Get task results for a student
- **GET /student/task/{task}**: Get task information

### Teacher Interface

- **POST /teacher/task/create**: Create a new task
- **GET /teacher**: Get information about the teacher interface
- **GET /teacher/task/results/{task}**: Get results for a task
- **DELETE /teacher/task/delete/{task}**: Delete a task
- **GET /teacher/task/{task}**: Get task information

## Deployment

### Prerequisites

- Kubernetes cluster
- kubectl configured to communicate with the cluster
- Docker for building images

### Building Images

```bash
# Build the API server image
docker build -t school-api:latest -f api/Dockerfile ./api

# Build the task pod image
docker build -t school-task:latest -f api/Dockerfile.slave ./api
```

### Deploying to Kubernetes

```bash
# Apply the Kubernetes manifests
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/task-pvc.yaml
```

## Usage

### For Teachers

1. Create a new task using the `/teacher/task/create` endpoint
2. Upload a validation script for the task
3. Monitor student submissions and results

### For Students

1. View available tasks using the `/student/task/{task}` endpoint
2. Submit solutions using the `/student/validate` endpoint
3. Check results using the `/student/task/result/{task}/{name}` endpoint

## Data Storage

The application uses persistent volumes for:

1. PostgreSQL database data
2. API server data (tasks, results, etc.)
3. Task pod data (input files, output files, etc.)

## Security Considerations

- The application uses basic authentication for students and teachers
- Task pods run with limited permissions
- Sensitive data is stored in the database, not in files

## Troubleshooting

- Check the logs of the API server pod: `kubectl logs -l app=api`
- Check the logs of the PostgreSQL pod: `kubectl logs -l app=postgres`
- Check the logs of a specific task pod: `kubectl logs -l task=<task-name>` 