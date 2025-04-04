#!/bin/bash
set -e

# Get environment variables
TASK_NAME=${TASK_NAME:-"default"}
STUDENT_NAME=${STUDENT_NAME:-"default"}
TEACHER_SCRIPT=${TEACHER_SCRIPT:-"/app/scripts/teacher_script.py"}
STUDENT_SCRIPT=${STUDENT_SCRIPT:-"/app/scripts/student_script.py"}
OUTPUT_DIR=${OUTPUT_DIR:-"/app/output"}

echo "Starting task validation for student: $STUDENT_NAME"
echo "Task: $TASK_NAME"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run teacher's script and capture output
echo "Running teacher's script..."
python3 "$TEACHER_SCRIPT" > "$OUTPUT_DIR/teacher_output.txt" 2>&1
TEACHER_EXIT_CODE=$?

# Run student's script and capture output
echo "Running student's script..."
python3 "$STUDENT_SCRIPT" > "$OUTPUT_DIR/student_output.txt" 2>&1
STUDENT_EXIT_CODE=$?

# Compare outputs
if [ $TEACHER_EXIT_CODE -eq 0 ] && [ $STUDENT_EXIT_CODE -eq 0 ]; then
    if diff "$OUTPUT_DIR/teacher_output.txt" "$OUTPUT_DIR/student_output.txt" > /dev/null; then
        echo "Validation successful: Outputs match"
        echo "SUCCESS" > "$OUTPUT_DIR/result.txt"
    else
        echo "Validation failed: Outputs differ"
        echo "FAIL" > "$OUTPUT_DIR/result.txt"
        diff "$OUTPUT_DIR/teacher_output.txt" "$OUTPUT_DIR/student_output.txt" > "$OUTPUT_DIR/diff.txt"
    fi
else
    echo "Validation failed: Script execution error"
    echo "ERROR" > "$OUTPUT_DIR/result.txt"
    echo "Teacher exit code: $TEACHER_EXIT_CODE" >> "$OUTPUT_DIR/result.txt"
    echo "Student exit code: $STUDENT_EXIT_CODE" >> "$OUTPUT_DIR/result.txt"
fi

# Write completion marker
echo "COMPLETED" > "$OUTPUT_DIR/status.txt"

# Keep the container running for a while to allow the API to fetch the results
sleep 30 