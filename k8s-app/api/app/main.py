from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import shutil
import json
import subprocess
from kubernetes import client, config
from pathlib import Path
import time
import asyncio
import yaml

app = FastAPI()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/school_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Base directories
BASE_DIR = Path("/data")
TASKS_DIR = BASE_DIR / "tasks"
RESULTS_DIR = BASE_DIR / "results"
TEACHERS_DIR = BASE_DIR / "teachers"
STUDENTS_DIR = BASE_DIR / "students"

# Create directories if they don't exist
for directory in [BASE_DIR, TASKS_DIR, RESULTS_DIR, TEACHERS_DIR, STUDENTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database Models
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    password = Column(String)

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    password = Column(String)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class TaskResult(Base):
    __tablename__ = "task_results"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    status = Column(String)  # SUCCESS, FAIL, ERROR
    created_at = Column(DateTime, default=datetime.utcnow)
    teacher_output = Column(String)
    student_output = Column(String)
    diff_output = Column(String, nullable=True)

# Pydantic Models
class StudentBase(BaseModel):
    name: str
    password: str

class TeacherBase(BaseModel):
    name: str
    password: str

class TaskBase(BaseModel):
    name: str
    description: str

class TaskResultBase(BaseModel):
    status: str
    teacher_output: str
    student_output: str
    diff_output: Optional[str] = None

class APIInfo(BaseModel):
    status: str
    endpoints: List[Dict[str, str]]

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)

# Kubernetes configuration
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

# Helper functions
def create_task_directory(task_name: str) -> Path:
    task_dir = TASKS_DIR / task_name
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir

def create_student_directory(student_name: str) -> Path:
    student_dir = STUDENTS_DIR / student_name
    student_dir.mkdir(parents=True, exist_ok=True)
    return student_dir

def create_result_directory(task_name: str, student_name: str) -> Path:
    result_dir = RESULTS_DIR / task_name / student_name
    result_dir.mkdir(parents=True, exist_ok=True)
    return result_dir

def create_teacher_directory(teacher_name: str) -> Path:
    teacher_dir = TEACHERS_DIR / teacher_name
    teacher_dir.mkdir(parents=True, exist_ok=True)
    return teacher_dir

def create_shared_pvc() -> str:
    """Create a shared PVC for input and output."""
    shared_pvc_name = "shared-pvc"
    shared_pvc = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": shared_pvc_name,
            "namespace": "default"
        },
        "spec": {
            "accessModes": ["ReadWriteMany"],
            "resources": {
                "requests": {
                    "storage": "1Gi"
                }
            },
            "storageClassName": "standard"
        }
    }
    
    # Create the shared PVC
    try:
        v1.create_namespaced_persistent_volume_claim(namespace="default", body=shared_pvc)
        return shared_pvc_name
    except Exception as e:
        print(f"Error creating shared PVC: {str(e)}")
        return shared_pvc_name  # Assume it exists if creation fails

def create_task_pod(task_name: str, student_name: str, db: Session, shared_pvc_name: str) -> str:
    try:
        # Generate unique pod name that follows Kubernetes naming conventions
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Sanitize task_name and student_name to ensure they only contain valid characters
        sanitized_task_name = ''.join(c.lower() if c.isalnum() else '-' for c in task_name)
        sanitized_student_name = ''.join(c.lower() if c.isalnum() else '-' for c in student_name)
        
        # Ensure the name starts and ends with alphanumeric characters
        sanitized_task_name = sanitized_task_name.strip('-')
        sanitized_student_name = sanitized_student_name.strip('-')
        
        # If sanitized names are empty, use a default value
        if not sanitized_task_name:
            sanitized_task_name = "task"
        if not sanitized_student_name:
            sanitized_student_name = "student"
        
        # Create a valid pod name
        pod_name = f"task-{sanitized_task_name}-{sanitized_student_name}-{timestamp}"
        
        # Ensure the pod name is not too long (Kubernetes has a limit of 63 characters)
        if len(pod_name) > 63:
            # Truncate the name while keeping the prefix and suffix
            prefix = "task-"
            suffix = f"-{timestamp}"
            max_middle_length = 63 - len(prefix) - len(suffix)
            middle = f"{sanitized_task_name}-{sanitized_student_name}"
            if len(middle) > max_middle_length:
                middle = middle[:max_middle_length]
            pod_name = f"{prefix}{middle}{suffix}"
        
        pod_template = f"""
apiVersion: v1
kind: Pod
metadata:
  name: {pod_name}
  labels:
    app: task
    task: {sanitized_task_name}
    student: {sanitized_student_name}
spec:
  containers:
    - name: task
      image: python:3.9-slim
      imagePullPolicy: IfNotPresent
      command: ["/bin/sh"]
      args: ["-c", "/shared/input/{task_name}/script/compare_scripts.sh"]
      env:
        - name: TASK_NAME
          value: {task_name}
        - name: STUDENT_NAME
          value: {student_name}
      volumeMounts:
        - name: shared-volume
          mountPath: /shared
  volumes:
    - name: shared-volume
      persistentVolumeClaim:
        claimName: {shared_pvc_name}
  restartPolicy: Never
"""
        
        # Parse YAML to dict
        pod_dict = yaml.safe_load(pod_template)
        
        # Create pod using the API
        pod = v1.create_namespaced_pod(
            namespace="default",
            body=pod_dict
        )
        
        return pod_name
    except Exception as e:
        print(f"Error creating task pod: {str(e)}")
        return None

def run_validation_script(task_name: str, student_name: str, file_path: Path) -> Dict[str, Any]:
    try:
        # Create a validation script path
        validation_script = TASKS_DIR / task_name / "validate.sh"
        
        if not validation_script.exists():
            return {"status": "error", "message": "Validation script not found"}
        
        # Make the script executable
        os.chmod(validation_script, 0o755)
        
        # Run the validation script
        result = subprocess.run(
            [str(validation_script), str(file_path)],
            capture_output=True,
            text=True
        )
        
        # Save the result
        result_file = create_result_directory(task_name, student_name) / "result.json"
        with open(result_file, "w") as f:
            json.dump({
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": result.stderr
            }, f)
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_task_pod_status(pod_name: str) -> Dict[str, Any]:
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace="default")
        status = {
            "phase": pod.status.phase,
            "completed": False,
            "result": None
        }
        
        if pod.status.phase == "Succeeded" or pod.status.phase == "Failed":
            # Check if output files exist
            try:
                # Try to cat the status file
                result = v1.read_namespaced_pod_exec(
                    name=pod_name,
                    namespace="default",
                    command=["cat", "/app/output/status.txt"]
                )
                if result and "COMPLETED" in result:
                    status["completed"] = True
                    # Get results
                    try:
                        result_text = v1.read_namespaced_pod_exec(
                            name=pod_name,
                            namespace="default",
                            command=["cat", "/app/output/result.txt"]
                        )
                        status["result"] = result_text.strip()
                    except:
                        status["result"] = "ERROR"
            except:
                # If we can't exec into the pod (e.g. it's completed but container terminated)
                # we consider it completed but with an error
                if pod.status.phase == "Succeeded":
                    status["completed"] = True
                    status["result"] = "ERROR"
        
        return status
    except Exception as e:
        print(f"Error checking pod status: {str(e)}")
        return {"phase": "Unknown", "completed": False, "result": None}

def collect_task_results(pod_name: str, task_name: str, student_name: str) -> Dict[str, str]:
    try:
        # Create result directory
        result_dir = create_result_directory(task_name, student_name)
        
        # Copy output files from pod
        for file in ["teacher_output.txt", "student_output.txt", "result.txt", "diff.txt"]:
            try:
                content = v1.read_namespaced_pod_exec(
                    name=pod_name,
                    namespace="default",
                    command=["cat", f"/app/output/{file}"]
                )
                with open(result_dir / file, "w") as f:
                    f.write(content)
            except:
                pass
        
        # Read results
        results = {}
        for file in ["teacher_output.txt", "student_output.txt", "result.txt", "diff.txt"]:
            if (result_dir / file).exists():
                with open(result_dir / file, "r") as f:
                    results[file] = f.read()
        
        # Delete the pod
        v1.delete_namespaced_pod(name=pod_name, namespace="default")
        
        return results
    except Exception as e:
        print(f"Error collecting task results: {str(e)}")
        return {}

# Background task to check and collect results
async def check_task_pods():
    while True:
        try:
            db = SessionLocal()
            # Get all running task pods
            pods = v1.list_namespaced_pod(
                namespace="default",
                label_selector="app=task"
            )
            
            for pod in pods.items:
                task_name = pod.metadata.labels.get("task")
                student_name = pod.metadata.labels.get("student")
                
                if task_name and student_name:
                    # Check if pod has completed
                    if pod.status.phase == "Succeeded" or pod.status.phase == "Failed":
                        # Read the output file
                        output_path = Path(f"/shared/output/{task_name}/{student_name}/output.txt")
                        status_path = Path(f"/shared/output/{task_name}/{student_name}/status.txt")
                        
                        if output_path.exists() and status_path.exists():
                            # Read the output file
                            with open(output_path, "r") as f:
                                output_content = f.read()
                            
                            # Parse the output to extract teacher and student outputs
                            teacher_output = ""
                            student_output = ""
                            diff_output = ""
                            status = "ERROR"
                            
                            # Split the output into sections
                            sections = output_content.split("=== ")
                            for section in sections:
                                if section.startswith("Teacher's Script Output"):
                                    teacher_output = section.split("\n", 1)[1].strip()
                                elif section.startswith("Student's Script Output"):
                                    student_output = section.split("\n", 1)[1].strip()
                                elif section.startswith("Comparison Results"):
                                    comparison = section.split("\n", 1)[1].strip()
                                    if "SUCCESS" in comparison:
                                        status = "SUCCESS"
                                    elif "FAIL" in comparison:
                                        status = "FAIL"
                                        # Extract diff if present
                                        if "=== Differences ===" in comparison:
                                            diff_output = comparison.split("=== Differences ===")[1].strip()
                            
                            # Get task and student IDs
                            task = db.query(Task).filter(Task.name == task_name).first()
                            student = db.query(Student).filter(Student.name == student_name).first()
                            
                            if task and student:
                                # Create or update task result
                                task_result = TaskResult(
                                    task_id=task.id,
                                    student_id=student.id,
                                    status=status,
                                    teacher_output=teacher_output,
                                    student_output=student_output,
                                    diff_output=diff_output
                                )
                                db.add(task_result)
                                db.commit()
                            
                            # Delete the pod
                            try:
                                v1.delete_namespaced_pod(
                                    name=pod.metadata.name,
                                    namespace="default"
                                )
                            except Exception as e:
                                print(f"Error deleting pod {pod.metadata.name}: {str(e)}")
            
            db.close()
        except Exception as e:
            print(f"Error in check_task_pods: {str(e)}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_task_pods())

@app.post("/student/validate")
async def validate_student_task(
    student_name: str = Form(...),
    task_name: str = Form(...),
    script_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate student
    student = db.query(Student).filter(Student.name == student_name).first()
    if not student:
        raise HTTPException(status_code=400, detail="Student not found")
    
    # Validate task
    task = db.query(Task).filter(Task.name == task_name).first()
    if not task:
        raise HTTPException(status_code=400, detail="Task not found")
    
    # Create directories
    student_dir = create_student_directory(student_name)
    task_dir = create_task_directory(task_name)
    
    # Save the student's script to shared input
    shared_input_dir = Path(f"/shared/input/{task_name}/{student_name}")
    shared_input_dir.mkdir(parents=True, exist_ok=True)
    student_script_path = shared_input_dir / f"{student_name}_script.py"
    with open(student_script_path, "wb") as buffer:
        shutil.copyfileobj(script_file.file, buffer)
    
    # Create shared PVC
    shared_pvc_name = create_shared_pvc()
    
    # Create and start task pod
    pod_name = create_task_pod(task_name, student_name, db, shared_pvc_name)
    if not pod_name:
        raise HTTPException(status_code=500, detail="Failed to create task pod")
    
    # Return information about the task
    return {
        "message": "Task validation started",
        "pod_name": pod_name,
        "status_url": f"/student/task/status/{pod_name}"
    }

# Add a new endpoint to check task status
@app.get("/student/task/status/{pod_name}")
def get_task_status(pod_name: str):
    status = check_task_pod_status(pod_name)
    return {
        "pod_name": pod_name,
        "status": status["phase"],
        "completed": status["completed"],
        "result": status["result"]
    }

@app.get("/student", response_model=APIInfo)
def get_student_info():
    endpoints = [
        {"path": "/student/validate", "description": "Upload and validate a student task"},
        {"path": "/student/task/result/{task}/{name}", "description": "Get task results for a student"},
        {"path": "/student/task/{task}", "description": "Get task information"}
    ]
    
    return APIInfo(
        status="active",
        endpoints=endpoints
    )

@app.get("/student/task/result/{task}/{name}")
def get_task_result(task: str, name: str, db: Session = Depends(get_db)):
    # Validate student
    student = db.query(Student).filter(Student.name == name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Validate task
    task_obj = db.query(Task).filter(Task.name == task).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get result from database
    result = db.query(TaskResult).filter(
        TaskResult.task_id == task_obj.id,
        TaskResult.student_id == student.id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {
        "status": result.status,
        "teacher_output": result.teacher_output,
        "student_output": result.student_output,
        "diff_output": result.diff_output,
        "created_at": result.created_at
    }

@app.get("/student/task/{task}")
def get_task(task: str, db: Session = Depends(get_db)):
    # Validate task
    task_obj = db.query(Task).filter(Task.name == task).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if task directory exists
    task_dir = TASKS_DIR / task
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail="Task directory not found")
    
    # Get task files
    task_files = [f.name for f in task_dir.iterdir() if f.is_file()]
    
    return {
        "name": task,
        "description": task_obj.description,
        "files": task_files,
        "path": str(task_dir)
    }

@app.post("/teacher/task/create")
async def create_task(
    task_name: str = Form(...),
    description: str = Form(...),
    teacher_name: str = Form(...),
    script_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate teacher
    teacher = db.query(Teacher).filter(Teacher.name == teacher_name).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Create task in database
    db_task = Task(
        name=task_name,
        description=description,
        teacher_id=teacher.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Create directories
    task_dir = create_task_directory(task_name)
    teacher_dir = create_teacher_directory(teacher_name)
    
    # Save the script file
    script_path = task_dir / "teacher_script.py"
    with open(script_path, "wb") as buffer:
        shutil.copyfileobj(script_file.file, buffer)
    
    # Create shared directories for the task
    shared_script_dir = Path(f"/shared/input/{task_name}/script")
    shared_script_dir.mkdir(parents=True, exist_ok=True)
    
    shared_teacher_dir = Path(f"/shared/input/{task_name}/teacher")
    shared_teacher_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy teacher's script to shared directory
    shutil.copy(str(script_path), str(shared_teacher_dir / "teacher_script.py"))
    
    # Copy the comparison script to shared script directory and make it executable
    script_template_path = Path(__file__).parent / "script_template.sh"
    compare_script_path = shared_script_dir / "compare_scripts.sh"
    shutil.copy(str(script_template_path), str(compare_script_path))
    compare_script_path.chmod(0o755)  # Make the script executable
    
    return {
        "message": "Task created successfully",
        "task_id": db_task.id
    }

@app.get("/teacher", response_model=APIInfo)
def get_teacher_info():
    endpoints = [
        {"path": "/teacher/task/create", "description": "Create a new task"},
        {"path": "/teacher/task/results/{task}", "description": "Get results for a task"},
        {"path": "/teacher/task/delete/{task}", "description": "Delete a task"},
        {"path": "/teacher/task/{task}", "description": "Get task information"}
    ]
    
    return APIInfo(
        status="active",
        endpoints=endpoints
    )

@app.get("/teacher/task/results/{task}")
def get_task_results(task: str, db: Session = Depends(get_db)):
    # Validate task
    task_obj = db.query(Task).filter(Task.name == task).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get all results for the task
    results = db.query(TaskResult).filter(TaskResult.task_id == task_obj.id).all()
    
    return [{
        "student_name": db.query(Student).filter(Student.id == r.student_id).first().name,
        "status": r.status,
        "created_at": r.created_at
    } for r in results]

@app.delete("/teacher/task/delete/{task}")
def delete_task(task: str, db: Session = Depends(get_db)):
    # Validate task
    task_obj = db.query(Task).filter(Task.name == task).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Delete container if it exists
        if task_obj.container_name:
            try:
                apps_v1.delete_namespaced_deployment(
                    name=task_obj.container_name,
                    namespace="default"
                )
            except:
                pass
        
        # Delete task directory
        task_dir = TASKS_DIR / task
        if task_dir.exists():
            shutil.rmtree(task_dir)
        
        # Delete results directory
        results_dir = RESULTS_DIR / task
        if results_dir.exists():
            shutil.rmtree(results_dir)
        
        # Delete PVCs for this task
        # We need to find all PVCs related to this task
        pvcs = v1.list_namespaced_persistent_volume_claim(
            namespace="default",
            label_selector=f"task={task}"
        )
        for pvc in pvcs.items:
            try:
                v1.delete_namespaced_persistent_volume_claim(
                    name=pvc.metadata.name,
                    namespace="default"
                )
            except:
                pass
        
        # Delete from database
        db.delete(task_obj)
        db.commit()
        
        return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

@app.get("/teacher/task/{task}")
def get_teacher_task(task: str, db: Session = Depends(get_db)):
    # Validate task
    task_obj = db.query(Task).filter(Task.name == task).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if task directory exists
    task_dir = TASKS_DIR / task
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail="Task directory not found")
    
    # Check if validation script exists
    validation_script = task_dir / "validate.sh"
    script_exists = validation_script.exists()
    
    # Check container status
    container_status = "not_created"
    if task_obj.container_name:
        try:
            pod = v1.read_namespaced_pod(name=task_obj.container_name, namespace="default")
            container_status = pod.status.phase
        except:
            container_status = "not_found"
    
    # Count results
    results_dir = RESULTS_DIR / task
    result_count = 0
    if results_dir.exists():
        result_count = len([d for d in results_dir.iterdir() if d.is_dir()])
    
    return {
        "name": task,
        "description": task_obj.description,
        "script_exists": script_exists,
        "container_status": container_status,
        "result_count": result_count,
        "path": str(task_dir)
    } 