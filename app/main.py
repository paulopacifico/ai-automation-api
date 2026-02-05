from fastapi import FastAPI

from app.api.tasks import router as tasks_router

app = FastAPI()

app.include_router(tasks_router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
