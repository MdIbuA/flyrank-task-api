from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# In-memory "database": lives only as long as the process does.
tasks: list[dict] = [
    {"id": 1, "title": "Read the FastAPI first-steps guide", "done": True},
    {"id": 2, "title": "Build the read endpoints", "done": False},
    {"id": 3, "title": "Push the repo to GitHub", "done": False},
]


def error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


def find_task(task_id: int) -> dict | None:
    return next((t for t in tasks if t["id"] == task_id), None)


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    return task
