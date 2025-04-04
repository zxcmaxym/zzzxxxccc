#!/bin/bash
docker build -t school-api:latest -f ./Dockerfile .
docker build -t school-task:latest -f ./Dockerfile.slave .
