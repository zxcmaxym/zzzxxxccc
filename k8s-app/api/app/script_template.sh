#!/bin/bash

# Create output directory
mkdir -p "/shared/output/$TASK_NAME/$STUDENT_NAME"

# Run teacher's script and capture output
TEACHER_OUTPUT=$(python3 "/shared/input/$TASK_NAME/teacher/teacher_script.py" 2>&1)
TEACHER_EXIT_CODE=$?

# Run student's script and capture output
STUDENT_OUTPUT=$(python3 "/shared/input/$TASK_NAME/$STUDENT_NAME/${STUDENT_NAME}_script.py" 2>&1)
STUDENT_EXIT_CODE=$?

# Compare outputs and write results
{
    echo "=== Teacher's Script Output ==="
    echo "$TEACHER_OUTPUT"
    echo -e "\n=== Student's Script Output ==="
    echo "$STUDENT_OUTPUT"
    echo -e "\n=== Comparison Results ==="
    
    if [ $TEACHER_EXIT_CODE -ne 0 ]; then
        echo "ERROR: Teacher's script failed with exit code $TEACHER_EXIT_CODE"
    elif [ $STUDENT_EXIT_CODE -ne 0 ]; then
        echo "ERROR: Student's script failed with exit code $STUDENT_EXIT_CODE"
    elif [ "$TEACHER_OUTPUT" = "$STUDENT_OUTPUT" ]; then
        echo "SUCCESS: Outputs match!"
    else
        echo "FAIL: Outputs do not match"
        echo -e "\n=== Differences ==="
        diff <(echo "$TEACHER_OUTPUT") <(echo "$STUDENT_OUTPUT")
    fi
} > "/shared/output/$TASK_NAME/$STUDENT_NAME/output.txt"

# Write completion status
echo "COMPLETED" > "/shared/output/$TASK_NAME/$STUDENT_NAME/status.txt"
