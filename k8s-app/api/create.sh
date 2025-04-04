#!/bin/bash
docker build -t student-api:latest -f ./Dockerfile .
docker build -t student-task:latest -f ./Dockerfile.slave .
