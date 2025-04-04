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
    container_name = Column(String, nullable=True)

class TaskResult(Base):
    __tablename__ = "task_results"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    result = Column(String)
    submitted_at = Column(DateTime, default=datetime.utcnow)

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
    result: str

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

def create_container_for_task(task_name: str, db: Session) -> bool:
    try:
        # Check if container already exists
        task = db.query(Task).filter(Task.name == task_name).first()
        if task and task.container_name:
            # Check if container is running
            try:
                pod = v1.read_namespaced_pod(name=task.container_name, namespace="default")
                if pod.status.phase == "Running":
                    return True
            except:
                pass
        
        # Create a new container
        container_name = f"task-{task_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create Kubernetes deployment
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=container_name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={"app": container_name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": container_name}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=container_name,
                                image="python:3.9-slim",
                                command=["/bin/sh", "-c"],
                                args=["while true; do sleep 3600; done"],
                                volume_mounts=[
                                    client.V1VolumeMount(
                                        name="task-data",
                                        mount_path="/app/data"
                                    )
                                ]
                            )
                        ],
                        volumes=[
                            client.V1Volume(
                                name="task-data",
                                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                    claim_name="task-pvc"
                                )
                            )
                        ]
                    )
                )
            )
        )
        
        # Create the deployment
        apps_v1.create_namespaced_deployment(
            namespace="default",
            body=deployment
        )
        
        # Update task with container name
        if task:
            task.container_name = container_name
            db.commit()
        
        return True
    except Exception as e:
        print(f"Error creating container: {str(e)}")
        return False

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

# API Endpoints
@app.post("/student/validate")
async def validate_student_task(
    student_name: str = Form(...),
    task_name: str = Form(...),
    file: UploadFile = File(...),
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
    result_dir = create_result_directory(task_name, student_name)
    
    # Save the uploaded file
    file_path = student_dir / f"{task_name}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create and start container if needed
    if not create_container_for_task(task_name, db):
        raise HTTPException(status_code=500, detail="Failed to create or start container")
    
    # Run validation
    result = run_validation_script(task_name, student_name, file_path)
    
    # Save result to database
    task_result = TaskResult(
        task_id=task.id,
        student_id=student.id,
        result=json.dumps(result)
    )
    db.add(task_result)
    db.commit()
    
    return result

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
    
    # Check if result file exists
    result_file = RESULTS_DIR / task / name / "result.json"
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Read and return the result
    with open(result_file, "r") as f:
        result = json.load(f)
    
    return result

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
    script_path = task_dir / "validate.sh"
    with open(script_path, "wb") as buffer:
        shutil.copyfileobj(script_file.file, buffer)
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    
    # Create container for the task
    if not create_container_for_task(task_name, db):
        raise HTTPException(status_code=500, detail="Failed to create container")
    
    return {
        "message": "Task created successfully",
        "task_id": db_task.id,
        "container_name": db_task.container_name
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
    
    # Check if results directory exists
    results_dir = RESULTS_DIR / task
    if not results_dir.exists():
        raise HTTPException(status_code=404, detail="Results not found")
    
    # Get all student results
    results = {}
    for student_dir in results_dir.iterdir():
        if student_dir.is_dir():
            student_name = student_dir.name
            result_file = student_dir / "result.json"
            if result_file.exists():
                with open(result_file, "r") as f:
                    results[student_name] = json.load(f)
    
    return results

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