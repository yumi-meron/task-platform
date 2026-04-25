from celery import Celery

# redis://localhost:6380/0 
celery_app = Celery(
    "worker",
    broker="redis://127.0.0.1:6380/0",
    backend="redis://127.0.0.1:6380/0"
)

# This tells Celery to look for tasks in a file called tasks.py
celery_app.autodiscover_tasks(["app.worker"])