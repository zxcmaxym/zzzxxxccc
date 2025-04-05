#!/bin/bash
POD_NAME=$(kubectl get pod -l app=postgres -o jsonpath="{.items[0].metadata.name}")

kubectl exec -it "$POD_NAME" -- bash -c "psql -U postgres -d school_db -c \"
INSERT INTO teachers (id, name, password) VALUES 
    (1, 'max', 'max'),
    (2, 'kolcak', 'kolcak');
INSERT INTO students (id, name, password) VALUES 
    (1, 'jozko', 'jozko'),
    (2, 'fero', 'fero'),
    (3, 'roman', 'roman'),
    (4, 'michal', 'michal');
\""

