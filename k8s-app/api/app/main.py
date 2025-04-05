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
import random

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
    teacher_output_path = Column(String)
    student_output_path = Column(String)

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class StudentGroup(Base):
    __tablename__ = "student_groups"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class TaskGroup(Base):
    __tablename__ = "task_groups"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

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

class APIInfo(BaseModel):
    status: str
    tasks: List[Dict[str, str]]
    endpoints: List[Dict[str, str]]

class GroupBase(BaseModel):
    name: str

class StudentGroupBase(BaseModel):
    student_name: str
    group_name: str

class TaskGroupBase(BaseModel):
    task_name: str
    group_name: str

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

def randomize_variables(task_name: str) -> List[int]:
    """Read variables from vars.txt and generate random values within the specified ranges."""
    vars_path = TASKS_DIR / task_name / "vars.txt"
    if not vars_path.exists():
        return []
    
    random_values = []
    with open(vars_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                start, end = map(int, line.split("-"))
                random_values.append(random.randint(start, end))
            except ValueError:
                continue
    
    return random_values

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
    
    # Validate script file is a Python file
    if not script_file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Script file must be a Python file (.py)")
    
    # Check if student has access to this task through their groups
    student_groups = db.query(StudentGroup).filter(StudentGroup.student_id == student.id).all()
    group_ids = [sg.group_id for sg in student_groups]
    
    task_groups = db.query(TaskGroup).filter(
        TaskGroup.task_id == task.id,
        TaskGroup.group_id.in_(group_ids)
    ).first()
    
    if not task_groups:
        raise HTTPException(status_code=403, detail="You don't have access to this task")
    
    # Generate random values for variables
    random_values = randomize_variables(task_name)
    
    # Check for existing results
    existing_result = db.query(TaskResult).filter(
        TaskResult.task_id == task.id,
        TaskResult.student_id == student.id
    ).first()
    
    if existing_result:
        # Delete existing result from database
        db.delete(existing_result)
        db.commit()
        
        # Delete old result files
        result_dir = RESULTS_DIR / task_name / student_name
        if result_dir.exists():
            shutil.rmtree(result_dir)
    
    # Create a new result with STARTED status
    task_result = TaskResult(
        task_id=task.id,
        student_id=student.id,
        status="STARTED",
        teacher_output_path="",
        student_output_path=""
    )
    db.add(task_result)
    db.commit()
    
    # Clean up old files and directories
    shared_input_dir = Path(f"/shared/input/{task_name}/{student_name}")
    if shared_input_dir.exists():
        shutil.rmtree(shared_input_dir)
    
    shared_output_dir = Path(f"/shared/output/{task_name}/{student_name}")
    if shared_output_dir.exists():
        shutil.rmtree(shared_output_dir)
    
    # Create directories
    student_dir = create_student_directory(student_name)
    task_dir = create_task_directory(task_name)
    
    # Save the student's script to shared input
    shared_input_dir.mkdir(parents=True, exist_ok=True)
    student_script_path = shared_input_dir / f"{student_name}_script.py"
    with open(student_script_path, "wb") as buffer:
        shutil.copyfileobj(script_file.file, buffer)
    
    # Save random values to vars.txt in shared directory
    if random_values:
        vars_path = shared_input_dir / "vars.txt"
        with open(vars_path, "w") as f:
            f.write("\n".join(map(str, random_values)))
    
    # Create shared PVC
    shared_pvc_name = create_shared_pvc()
    
    # Create and start task pod
    pod_name = create_task_pod(task_name, student_name, db, shared_pvc_name)
    if not pod_name:
        # If pod creation fails, update status to ERROR
        task_result.status = "ERROR"
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to create task pod")
    
    # Return information about the task
    return {
        "message": "Task validation started",
        "pod_name": pod_name,
        "result_url": f"/student/task/result/{task_name}/{student_name}"
    }

@app.get("/student/task/result/{task_name}/{student_name}")
def get_task_result(task_name: str, student_name: str, db: Session = Depends(get_db)):
    # Validate student
    student = db.query(Student).filter(Student.name == student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Validate task
    task = db.query(Task).filter(Task.name == task_name).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if student has access to this task through their groups
    student_groups = db.query(StudentGroup).filter(StudentGroup.student_id == student.id).all()
    group_ids = [sg.group_id for sg in student_groups]
    
    task_groups = db.query(TaskGroup).filter(
        TaskGroup.task_id == task.id,
        TaskGroup.group_id.in_(group_ids)
    ).first()
    
    if not task_groups:
        raise HTTPException(status_code=403, detail="You don't have access to this task")
    
    # Get most recent task result from database
    task_result = db.query(TaskResult).filter(
        TaskResult.task_id == task.id,
        TaskResult.student_id == student.id
    ).order_by(TaskResult.created_at.desc()).first()
    
    if not task_result:
        return {
            "result": "NOT_STARTED",
            "output": None
        }
    
    # Read the output file
    output_path = Path(f"/shared/output/{task_name}/{student_name}/output.txt")
    if not output_path.exists():
        return {
            "result": task_result.status,
            "output": None
        }
    
    try:
        with open(output_path, "r") as f:
            output_content = f.read()
        return {
            "result": task_result.status,  # SUCCESS, FAIL, ERROR, or NOT_STARTED
            "output": output_content
        }
    except Exception as e:
        return {
            "result": task_result.status,
            "output": None,
            "error": str(e)
        }

@app.get("/student", response_model=APIInfo)
def get_student_info(name: str, db: Session = Depends(get_db)):
    # Validate student
    student = db.query(Student).filter(Student.name == name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get student's groups
    student_groups = db.query(StudentGroup).filter(StudentGroup.student_id == student.id).all()
    group_ids = [sg.group_id for sg in student_groups]
    
    # Get tasks assigned to these groups
    task_groups = db.query(TaskGroup).filter(TaskGroup.group_id.in_(group_ids)).all()
    task_ids = [tg.task_id for tg in task_groups]
    
    # Get task details
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
    
    # Get most recent results for these tasks
    results = db.query(TaskResult).filter(
        TaskResult.task_id.in_(task_ids),
        TaskResult.student_id == student.id
    ).order_by(TaskResult.created_at.desc()).all()
    
    # Create result map for quick lookup (most recent result for each task)
    result_map = {}
    for r in results:
        if r.task_id not in result_map:  # Only keep the first (most recent) result for each task
            result_map[r.task_id] = r.status
    
    # Format task information
    task_info = []
    for task in tasks:
        task_info.append({
            "name": task.name,
            "description": task.description,
            "result": result_map.get(task.id, "NOT_STARTED")  # SUCCESS, FAIL, ERROR, or NOT_STARTED
        })
    
    return APIInfo(
        status="active",
        tasks=task_info,
        endpoints=[
            {"path": "/student/validate", "description": "Upload and validate a student task"},
            {"path": "/student/task/result/{task}/{name}", "description": "Get task result for a student"},
            {"path": "/student/task/{task}", "description": "Get task information"}
        ]
    )

@app.get("/student/task/{task}")
def get_task(task: str, name: str, db: Session = Depends(get_db)):
    # Validate student
    student = db.query(Student).filter(Student.name == name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Validate task
    task_obj = db.query(Task).filter(Task.name == task).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if student has access to this task
    student_groups = db.query(StudentGroup).filter(StudentGroup.student_id == student.id).all()
    group_ids = [sg.group_id for sg in student_groups]
    
    task_groups = db.query(TaskGroup).filter(
        TaskGroup.task_id == task_obj.id,
        TaskGroup.group_id.in_(group_ids)
    ).first()
    
    if not task_groups:
        raise HTTPException(status_code=403, detail="You don't have access to this task")
    
    # Check if task directory exists
    task_dir = TASKS_DIR / task
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail="Task directory not found")
    
    # Get task files
    task_files = [f.name for f in task_dir.iterdir() if f.is_file()]
    
    # Get most recent result if exists
    result = db.query(TaskResult).filter(
        TaskResult.task_id == task_obj.id,
        TaskResult.student_id == student.id
    ).order_by(TaskResult.created_at.desc()).first()
    
    return {
        "name": task,
        "description": task_obj.description,
        "files": task_files,
        "path": str(task_dir),
        "status": result.status if result else "NOT_STARTED"
    }

@app.post("/teacher/task/create")
async def create_task(
    task_name: str = Form(...),
    description: str = Form(...),
    teacher_name: str = Form(...),
    group_names: List[str] = Form(...),
    script_file: UploadFile = File(...),
    variables_file: UploadFile = File(None),  # New optional file upload
    db: Session = Depends(get_db)
):
    # Validate teacher
    teacher = db.query(Teacher).filter(Teacher.name == teacher_name).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Check if task with same name already exists
    existing_task = db.query(Task).filter(Task.name == task_name).first()
    if existing_task:
        raise HTTPException(status_code=400, detail="A task with this name already exists")
    
    # Validate script file is a Python file
    if not script_file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Script file must be a Python file (.py)")
    
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
    
    # Save the variables file if provided
    if variables_file:
        vars_path = task_dir / "vars.txt"
        with open(vars_path, "wb") as buffer:
            shutil.copyfileobj(variables_file.file, buffer)
    
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
    
    # Assign task to groups
    for group_name in group_names:
        # Validate group
        group = db.query(Group).filter(
            Group.name == group_name,
            Group.teacher_id == teacher.id
        ).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"Group {group_name} not found")
        
        # Create task-group association
        db_task_group = TaskGroup(
            task_id=db_task.id,
            group_id=group.id
        )
        db.add(db_task_group)
    
    db.commit()
    
    return {
        "message": "Task created successfully",
        "task_id": db_task.id
    }

@app.get("/teacher", response_model=APIInfo)
def get_teacher_info(db: Session = Depends(get_db)):
    endpoints = [
        {"path": "/teacher/task/create", "description": "Create a new task"},
        {"path": "/teacher/task/results/{task}", "description": "Get results for a task"},
        {"path": "/teacher/task/delete/{task}", "description": "Delete a task"},
        {"path": "/teacher/task/{task}", "description": "Get task information"},
        {"path": "/teacher/group/create", "description": "Create a new group"},
        {"path": "/teacher/group/add-student", "description": "Add a student to a group"},
        {"path": "/teacher/group/{group}/students", "description": "Get students in a group"},
        {"path": "/teacher/group/{group}/tasks", "description": "Get tasks assigned to a group"}
    ]
    
    return APIInfo(
        status="active",
        tasks=[],  # Empty list since this endpoint doesn't return any tasks
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
        "result": r.status,  # SUCCESS, FAIL, ERROR, or NOT_STARTED
        "created_at": r.created_at
    } for r in results]

@app.delete("/teacher/task/delete/{task}")
def delete_task(task: str, db: Session = Depends(get_db)):
    # Validate task
    task_obj = db.query(Task).filter(Task.name == task).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Delete task directory
        task_dir = TASKS_DIR / task
        if task_dir.exists():
            shutil.rmtree(task_dir)
        
        # Delete results directory
        results_dir = RESULTS_DIR / task
        if results_dir.exists():
            shutil.rmtree(results_dir)
        
        # Delete shared directories
        shared_task_dir = Path(f"/shared/input/{task}")
        if shared_task_dir.exists():
            shutil.rmtree(shared_task_dir)
        
        shared_output_dir = Path(f"/shared/output/{task}")
        if shared_output_dir.exists():
            shutil.rmtree(shared_output_dir)
        
        # Delete any running task pods for this task
        pods = v1.list_namespaced_pod(
            namespace="default",
            label_selector=f"app=task,task={task}"
        )
        for pod in pods.items:
            try:
                v1.delete_namespaced_pod(
                    name=pod.metadata.name,
                    namespace="default"
                )
            except:
                pass
        
        # Delete task results from database
        db.query(TaskResult).filter(TaskResult.task_id == task_obj.id).delete()
        
        # Delete task groups first
        db.query(TaskGroup).filter(TaskGroup.task_id == task_obj.id).delete()
        
        # Delete task from database
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
    
    # Get task files
    task_files = [f.name for f in task_dir.iterdir() if f.is_file()]
    
    # Count results
    results_dir = RESULTS_DIR / task
    result_count = 0
    if results_dir.exists():
        result_count = len([d for d in results_dir.iterdir() if d.is_dir()])
    
    return {
        "name": task,
        "description": task_obj.description,
        "files": task_files,
        "result_count": result_count,
        "path": str(task_dir)
    }

@app.post("/teacher/group/create")
def create_group(group_name: str = Form(...), teacher_name: str = Form(...), db: Session = Depends(get_db)):
    # Validate teacher
    teacher = db.query(Teacher).filter(Teacher.name == teacher_name).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Check if group already exists
    existing_group = db.query(Group).filter(
        Group.name == group_name,
        Group.teacher_id == teacher.id
    ).first()
    
    if existing_group:
        raise HTTPException(status_code=400, detail="A group with this name already exists")
    
    # Create group
    db_group = Group(
        name=group_name,
        teacher_id=teacher.id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    return {"message": "Group created successfully", "group_id": db_group.id}

@app.post("/teacher/group/add-student")
def add_student_to_group(student_group: StudentGroupBase, teacher_name: str, db: Session = Depends(get_db)):
    # Validate teacher
    teacher = db.query(Teacher).filter(Teacher.name == teacher_name).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Validate student
    student = db.query(Student).filter(Student.name == student_group.student_name).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Validate group
    group = db.query(Group).filter(
        Group.name == student_group.group_name,
        Group.teacher_id == teacher.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if student is already in group
    existing = db.query(StudentGroup).filter(
        StudentGroup.student_id == student.id,
        StudentGroup.group_id == group.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Student is already in this group")
    
    # Add student to group
    db_student_group = StudentGroup(
        student_id=student.id,
        group_id=group.id
    )
    db.add(db_student_group)
    db.commit()
    
    return {"message": "Student added to group successfully"}

@app.get("/teacher/group/{group}/students")
def get_group_students(group: str, teacher_name: str, db: Session = Depends(get_db)):
    # Validate teacher
    teacher = db.query(Teacher).filter(Teacher.name == teacher_name).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Validate group
    group_obj = db.query(Group).filter(
        Group.name == group,
        Group.teacher_id == teacher.id
    ).first()
    if not group_obj:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get students in group
    student_groups = db.query(StudentGroup).filter(StudentGroup.group_id == group_obj.id).all()
    student_ids = [sg.student_id for sg in student_groups]
    students = db.query(Student).filter(Student.id.in_(student_ids)).all()
    
    return [{"name": student.name} for student in students]

@app.get("/teacher/group/{group}/tasks")
def get_group_tasks(group: str, teacher_name: str, db: Session = Depends(get_db)):
    # Validate teacher
    teacher = db.query(Teacher).filter(Teacher.name == teacher_name).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Validate group
    group_obj = db.query(Group).filter(
        Group.name == group,
        Group.teacher_id == teacher.id
    ).first()
    if not group_obj:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get tasks assigned to group
    task_groups = db.query(TaskGroup).filter(TaskGroup.group_id == group_obj.id).all()
    task_ids = [tg.task_id for tg in task_groups]
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
    
    return [{"name": task.name, "description": task.description} for task in tasks]