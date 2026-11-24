from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StrictBool, StrictStr, field_validator, model_validator

app = FastAPI()

# In-memory "database": lives only as long as the process does.
tasks: list[dict] = [
    {"id": 1, "title": "Read the FastAPI first-steps guide", "done": True},
    {"id": 2, "title": "Build the read endpoints", "done": False},
    {"id": 3, "title": "Push the repo to GitHub", "done": False},
]
next_id = 4


def clean_title(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("title must not be empty")
    return value


class TaskCreate(BaseModel):
    title: StrictStr

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        return clean_title(value)


class TaskUpdate(BaseModel):
    title: StrictStr | None = None
    done: StrictBool | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str | None) -> str | None:
        return None if value is None else clean_title(value)

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.title is None and self.done is None:
            raise ValueError("send at least one of: title, done")
        return self


def error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


def find_task(task_id: int) -> dict | None:
    return next((t for t in tasks if t["id"] == task_id), None)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # FastAPI answers bad input with 422 by default; this API uses 400 Bad Request
    # and a single readable message instead of Pydantic's error list.
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first["loc"] if part != "body")
    message = first["msg"].removeprefix("Value error, ")
    return error(400, f"{field}: {message}" if field else message)


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


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    global next_id
    task = {"id": next_id, "title": payload.title, "done": False}
    next_id += 1
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    if payload.title is not None:
        task["title"] = payload.title
    if payload.done is not None:
        task["done"] = payload.done
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    tasks.remove(task)
    return Response(status_code=204)
