#!/bin/bash
POD_NAME=$(kubectl get pod -l app=postgres -o jsonpath="{.items[0].metadata.name}")

kubectl exec -it "$POD_NAME" -- bash -c "psql -U postgres -d school_db -c \"INSERT INTO teachers VALUES (1, 'max', 'max'); INSERT INTO students VALUES (1, 'jozko', 'jozko');\""

