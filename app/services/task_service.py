from sqlalchemy.orm import Session
from uuid import UUID
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate
from app.models.task import TaskStatus
from app.db.redis import redis_client
import json


class TaskService:
    def __init__(self, db: Session):
        self.repository = TaskRepository(db)
        self.db = db
    
    def _get_queue_name(self, priority: int) -> str:
        """Helper to map integer priority value to queue names"""
        if priority >= 10:
            return "high"
        elif priority >= 5:
            return "medium"
        return "low"
    
    
    def create_task(self, task_in :TaskCreate):
        from app.worker.tasks import process_task # Its imported locally not to cause a circular import with worker.tasks
        # Business Logic: Prepare data for the repository
        task_data = task_in.model_dump()
        task_data["status"] = TaskStatus.pending
        task_data["retries"] = 0

        new_task =self.repository.create(task_data)

        # Determine target queue based on priority integer value
        target_queue = self._get_queue_name(new_task.priority)

        # Use apply_async instead of .delay() to specify the queue routing
        process_task.apply_async(args = [str(new_task.id)], queue= target_queue)


        # Trigger Celery (Notice we use .delay())
        # .delay() sends the task_id to Redis and returns immediately
        # process_task.delay(str(new_task.id))

        return new_task
    
    def get_task(self, task_id: UUID):
        cache_key = f"task:{task_id}"

        # 1. Look up the task in Redis
        try:
            cached_task = redis_client.get(cache_key)
            if cached_task:
                # Cache Hit! Convert the stored JSON string back into a dictionary
                print(f"--- [CACHE HIT] Fetching task {task_id} from Redis ---")
                return json.loads(cached_task)
        except Exception as e:
            # Operational Safety: If Redis fails, log it but don't crash the app
            print(f"Redis Error: {e}")
        
        # 2. Cache Miss: Query the slower database via repository
        print(f"--- [CACHE MISS] Fetching task {task_id} from PostgreSQL ---")
        task = self.repository.get_by_id(task_id)
        if not task:
            return None
        
        # 3. Save a copy back into Redis with a 5-minute TTL (300 seconds)
        # We manually serialize SQLAlchemy properties into JSON
        try:
            task_dict = {
                "id": str(task.id),
                "payload": task.payload,
                "status": task.status,
                "priority": task.priority,
                "retries": task.retries,
                "created_at": task.created_at.isoformat() if task.created_at else None
            }
            redis_client.setex(cache_key, 300, json.dumps(task_dict))
        except Exception as e:
            print(f"Failed to cache task:{e}")

        return task
    
    def get_all_tasks(self, limit: int, offset: int, status: str = None):
        tasks = self.repository.list(limit, offset, status)
        total = self.repository.count(status)
        return tasks, total
    
    def manual_retry(self, task_id: UUID):
        from app.worker.tasks import process_task

        task = self.repository.get_by_id(task_id)
        if not task: 
            return None
        if task.status != TaskStatus.failed:
            return task
        
        # Logic to reset and re-enqueue
        task.status = TaskStatus.pending
        task.retries = 0
        self.db.commit()

        # The task status just changed from FAILED back to PENDING. 
        # We purge the old cache key so users don't see the old 'FAILED' status on subsequent GETs
        try:
            redis_client.delete(f"task:{task_id}")
            print(f"--- [CACHE INVALIDATED] Cleared task {task_id} due to retry update ---")
        except Exception as e:
            print(f"Failed to clear cache: {e}")
    

        # Route to correct queue
        target_queue = self._get_queue_name(task.priority)
        process_task.apply_async(args=[str(task.id)], queue = target_queue)
        # process_task.delay(str(task.id))
        return task
