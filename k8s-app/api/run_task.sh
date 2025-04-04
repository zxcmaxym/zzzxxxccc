#!/bin/bash
set -e

# Get the task name from environment variable
TASK_NAME=${TASK_NAME:-"default"}
INPUT_FILE=${INPUT_FILE:-"/app/data/input.txt"}
OUTPUT_FILE=${OUTPUT_FILE:-"/app/data/output.txt"}

echo "Starting task: $TASK_NAME"
echo "Processing input file: $INPUT_FILE"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
  echo "Error: Input file $INPUT_FILE does not exist"
  exit 1
fi

# Create output directory if it doesn't exist
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

# Execute the task
# This is a placeholder - the actual task execution will depend on the specific task
# The task script will be mounted from the task directory
TASK_SCRIPT="/app/data/task_script.sh"

if [ -f "$TASK_SCRIPT" ]; then
  chmod +x "$TASK_SCRIPT"
  "$TASK_SCRIPT" "$INPUT_FILE" "$OUTPUT_FILE"
  EXIT_CODE=$?
else
  echo "Error: Task script $TASK_SCRIPT does not exist"
  exit 1
fi

# Check if the task was successful
if [ $EXIT_CODE -ne 0 ]; then
  echo "Error: Task failed with exit code $EXIT_CODE"
  exit $EXIT_CODE
fi

echo "Task completed successfully"
echo "Output written to: $OUTPUT_FILE"

# Keep the container running for a while to allow the API to fetch the results
sleep 30 