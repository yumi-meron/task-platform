from celery import Celery
from kombu import Queue

# redis://localhost:6380/0 
celery_app = Celery(
    "worker",
    broker="redis://127.0.0.1:6380/0",
    backend="redis://127.0.0.1:6380/0"
)

# Define the explicit physical queuea inside our broker
celery_app.conf.task_queues = (
    Queue("high"),
    Queue("medium"),
    Queue("low"),
)

# Set a default queue fallback for tasks that didn't specify one
celery_app.conf.task_default_queue = "medium"

# This tells Celery to look for tasks in a file called tasks.py
celery_app.autodiscover_tasks(["app.worker"])