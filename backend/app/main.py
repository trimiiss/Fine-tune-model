import shutil
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

from app.routes import datasets, experiments, playground
from app.services.storage import MODEL_DIR, store

app = FastAPI(title="Fine-Tuning Studio API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(datasets.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(playground.router, prefix="/api")


class ModelImportRequest(BaseModel):
    model_id: str = Field(min_length=1)
    source_path: str = Field(min_length=1)


@app.post("/api/models/import")
def import_model(payload: ModelImportRequest) -> dict:
    catalog_entry = next((model for model in store.models() if model["id"] == payload.model_id), None)
    if not catalog_entry:
        raise HTTPException(404, "Model is not in the local catalog")
    source = Path(payload.source_path).expanduser()
    if not source.is_dir():
        raise HTTPException(400, "Source path must be an existing model folder")
    if not (source / "config.json").exists():
        raise HTTPException(400, "The source folder does not contain config.json")
    target = MODEL_DIR / payload.model_id.replace("/", "--")
    if source.resolve() == target.resolve():
        return next(model for model in store.models() if model["id"] == payload.model_id)
    try:
        shutil.copytree(source, target, dirs_exist_ok=True)
    except OSError as exc:
        raise HTTPException(500, f"Could not import model files: {exc}") from exc
    return next(model for model in store.models() if model["id"] == payload.model_id)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "fine-tuning-studio", "runtime": store.runtime_summary()}


@app.get("/api/models")
def models() -> list[dict]:
    return store.models()


@app.get("/api/dashboard")
def dashboard() -> dict:
    return store.dashboard()
