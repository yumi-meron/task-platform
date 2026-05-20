import time, random
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.task import Task, TaskStatus
from app.db.redis import redis_client

@celery_app.task(bind=True,name= "process_task", max_retries=3, soft_time_linit=30) #timeout after 30 seconds

def process_task(self, task_id: str): # task_id is str for Celery/JSON compatibility
    db = SessionLocal()
    task = None
    try:
        # 1. Fetch the task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return "Task not found"

        # If the task is already processing or completed, stop immediately.
        if task.status in [TaskStatus.completed, TaskStatus.processing]:
            return f"Task {task_id} is already {task.status}. Skipping."
        
        # 2. Mark as processing
        task.status = TaskStatus.processing
        db.commit()

        redis_client.delete(f"task:{task_id}")

        # 3. Simulate work and failure 
        time.sleep(5)
        if random.random() < 0.2 :
            raise Exception("Random Simulation Failure!")

        # 4. Mark as completed
        task.status = TaskStatus.completed
        db.commit()
        redis_client.delete(f"task:{task_id}")
        return f"Task {task_id} finished successfully"
    
    except Exception as e:
        if task:
            task.status = TaskStatus.pending
            # Update the DB with the current retry count
            task.retries = self.request.retries + 1
            db.commit()
            redis_client.delete(f"task:{task_id}")

        # Exponential Backoff: 2^retries * 2 (2s, 4s, 8s...)
        retry_delay = (2 ** self.request.retries) * 2

        # Check if we should try again or give up
        if self.request.retries < self.max_retries:
            db.close()
            raise self.retry(exc = e, countdown=retry_delay)
        else:
            task.status = TaskStatus.failed
            db.commit()
            redis_client.delete(f"task:{task_id}")
            return "MAx retries reached. Task failed."    
    finally:
        db.close()

