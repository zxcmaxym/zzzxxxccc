#!/usr/bin/env python3
import sys
import json
import os

def convert_output_to_json(task_name, student_name):
    """
    Convert the plain text output to JSON format.
    
    Args:
        task_name: Name of the task
        student_name: Name of the student
    
    Returns:
        JSON string containing the structured output
    """
    output_path = f"/shared/output/{task_name}/{student_name}/output.txt"
    status_path = f"/shared/output/{task_name}/{student_name}/status.txt"
    
    if not os.path.exists(output_path):
        return json.dumps({
            "error": "Output file not found"
        })
    
    try:
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Parse the content
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line == "TEACHER OUTPUT:":
                current_section = "teacher_output"
                current_content = []
            elif line == "STUDENT OUTPUT:":
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "student_output"
                current_content = []
            elif line == "DIFF:":
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "diff"
                current_content = []
            elif line == "PATTERN SEARCH:":
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "pattern_search"
                current_content = []
            elif line.startswith("SUCCESS:") or line.startswith("FAIL:") or line.startswith("ERROR:"):
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "comparison_result"
                current_content = [line]
            elif line.startswith("  Pattern:"):
                if current_section == "pattern_search":
                    current_content.append(line)
            elif current_section:
                current_content.append(line)
        
        # Add the last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        # Extract comparison result
        comparison_result = "UNKNOWN"
        if "comparison_result" in sections:
            result_text = sections["comparison_result"]
            if "SUCCESS" in result_text:
                comparison_result = "SUCCESS"
            elif "FAIL" in result_text:
                comparison_result = "FAIL"
            elif "ERROR" in result_text:
                comparison_result = "ERROR"
        
        # Parse pattern search results
        patterns = []
        if "pattern_search" in sections:
            pattern_lines = sections["pattern_search"].split('\n')
            for line in pattern_lines:
                if line.startswith("  Pattern:"):
                    parts = line.split(" - ")
                    if len(parts) == 2:
                        pattern = parts[0].replace("  Pattern: ", "").strip('"')
                        result = parts[1]
                        found = "FOUND" in result
                        count = 0
                        if found and "(" in result and ")" in result:
                            try:
                                count_str = result.split("(")[1].split(" ")[0]
                                count = int(count_str)
                            except (IndexError, ValueError):
                                # If parsing fails, just use 0
                                pass
                        patterns.append({
                            "pattern": pattern,
                            "found": found,
                            "count": count
                        })
        
        # Create the JSON structure
        result = {
            "teacher_output": sections.get("teacher_output", ""),
            "student_output": sections.get("student_output", ""),
            "comparison_result": {
                "status": comparison_result,
                "message": sections.get("comparison_result", ""),
                "diff": sections.get("diff", "")
            },
            "pattern_search": {
                "patterns": patterns
            }
        }
        
        # Write the JSON to a file
        json_path = f"/shared/output/{task_name}/{student_name}/output.json"
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return json.dumps(result)
    
    except Exception as e:
        return json.dumps({
            "error": f"Error converting output to JSON: {str(e)}"
        })

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(json.dumps({"error": "Usage: convert_to_json.py <task_name> <student_name>"}))
        sys.exit(1)
    
    task_name = sys.argv[1]
    student_name = sys.argv[2]
    
    result = convert_output_to_json(task_name, student_name)
    print(result) 