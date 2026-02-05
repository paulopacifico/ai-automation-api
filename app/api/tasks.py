from fastapi import APIRouter

router = APIRouter()


@router.post("/tasks")
def create_task() -> dict:
    return {"id": "task_123", "status": "created"}


@router.get("/tasks/{id}")
def get_task(id: str) -> dict:
    return {"id": id, "status": "pending"}
