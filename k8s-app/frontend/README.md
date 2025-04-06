# School Task Management Frontend

This is the frontend application for the School Task Management System. It provides an interface for students and teachers to interact with the tasks and assignments.

## Features

### Student Interface

- View assigned tasks
- View task details
- Submit task solutions
- View task results

### Teacher Interface

- Create and manage tasks
- Create and manage student groups
- Assign tasks to groups
- View task results for all students

## Development

### Prerequisites

- Node.js 14+ and npm
- Docker (for building and running the container)
- Kubernetes cluster with kubectl configured

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The application will be available at http://localhost:3000.

### Building the Docker Image

```bash
# Build the image
docker build -t school-frontend:latest .
```

### Deploying to Kubernetes

```bash
# Apply the Kubernetes deployment
kubectl apply -f ../k8s/frontend-deployment.yaml
```

Or use the provided build script:

```bash
# Run the build and deploy script
chmod +x build.sh
./build.sh
```

## Configuration

The frontend is configured to connect to the API server using the environment variable `REACT_APP_API_URL`. In the Kubernetes deployment, this is set to `http://api:8000`.

## Architecture

The frontend is built with:

- React for UI components
- React Router for navigation
- Material UI for component library
- Axios for API calls

The application is containerized using Docker and deployed to Kubernetes. 