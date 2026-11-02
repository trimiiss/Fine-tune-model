from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import datasets, experiments, playground
from app.services.storage import store

app = FastAPI(title="Fine-Tuning Studio API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(datasets.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(playground.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "fine-tuning-studio", "runtime": store.runtime_summary()}


@app.get("/api/models")
def models() -> list[dict]:
    return store.models()


@app.get("/api/dashboard")
def dashboard() -> dict:
    return store.dashboard()
