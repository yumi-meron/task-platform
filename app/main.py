from fastapi import FastAPI
from app.api.endpoints import tasks

app = FastAPI(title= "Task Management Platform")

app.include_router(tasks.router)

@app.get("/health")
def health_check():
    return {"status" : "OK"}

