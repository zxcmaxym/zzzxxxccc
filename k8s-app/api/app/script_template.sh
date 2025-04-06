#!/bin/bash

# Get task name and student name from environment variables
TASK_NAME=$1
STUDENT_NAME=$2

# Set up directories
INPUT_DIR="/shared/input/$TASK_NAME"
OUTPUT_DIR="/shared/output/$TASK_NAME/$STUDENT_NAME"
mkdir -p $OUTPUT_DIR

# Run teacher's script and capture output
echo "Running teacher's script..."
TEACHER_OUTPUT=$(python3 $INPUT_DIR/teacher/teacher_script.py 2>&1)
TEACHER_EXIT_CODE=$?

# Run student's script and capture output
echo "Running student's script..."
STUDENT_OUTPUT=$(python3 $INPUT_DIR/$STUDENT_NAME/${STUDENT_NAME}_script.py 2>&1)
STUDENT_EXIT_CODE=$?

# Write outputs to output.txt
echo "TEACHER OUTPUT:" > $OUTPUT_DIR/output.txt
echo "$TEACHER_OUTPUT" >> $OUTPUT_DIR/output.txt
echo "" >> $OUTPUT_DIR/output.txt
echo "STUDENT OUTPUT:" >> $OUTPUT_DIR/output.txt
echo "$STUDENT_OUTPUT" >> $OUTPUT_DIR/output.txt
echo "" >> $OUTPUT_DIR/output.txt

# Compare outputs
if [ "$TEACHER_OUTPUT" = "$STUDENT_OUTPUT" ]; then
    echo "SUCCESS: Outputs match!" >> $OUTPUT_DIR/output.txt
    echo "COMPLETED" > $OUTPUT_DIR/status.txt
else
    echo "FAIL: Outputs do not match" >> $OUTPUT_DIR/output.txt
    echo "COMPLETED" > $OUTPUT_DIR/status.txt
fi

# Check for patterns in find.txt if it exists
if [ -f "$INPUT_DIR/script/find.txt" ]; then
    echo "" >> $OUTPUT_DIR/output.txt
    echo "PATTERN SEARCH:" >> $OUTPUT_DIR/output.txt
    
    while IFS= read -r pattern; do
        # Count occurrences of pattern in student's script
        COUNT=$(grep -c "$pattern" "$INPUT_DIR/$STUDENT_NAME/${STUDENT_NAME}_script.py")
        if [ $COUNT -gt 0 ]; then
            echo "  Pattern: \"$pattern\" - FOUND ($COUNT occurrences)" >> $OUTPUT_DIR/output.txt
        else
            echo "  Pattern: \"$pattern\" - NOT FOUND" >> $OUTPUT_DIR/output.txt
        fi
    done < "$INPUT_DIR/script/find.txt"
fi

echo "COMPLETED" > $OUTPUT_DIR/status.txt
