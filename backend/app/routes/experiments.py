from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.services.storage import store
from app.training.pipeline import train_with_lora
from app.utils.dataset import load_and_validate

router = APIRouter(tags=["experiments"])


class TrainingConfig(BaseModel):
    epochs: int = Field(3, ge=1, le=20)
    batch_size: int = Field(4, ge=1, le=64)
    learning_rate: float = Field(2e-4, gt=0, le=1)
    lora_r: int = Field(16, ge=1, le=256)
    lora_alpha: int = Field(32, ge=1, le=512)
    max_length: int = Field(512, ge=32, le=4096)


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dataset_id: str
    model_id: str
    config: TrainingConfig


@router.get("/experiments")
def list_experiments() -> list[dict]:
    return store.list_experiments()


@router.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict:
    experiment = store.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(404, "Experiment not found")
    return experiment


@router.post("/experiments")
def create_experiment(payload: ExperimentCreate) -> dict:
    if not store.get_dataset(payload.dataset_id):
        raise HTTPException(404, "Dataset not found")
    if payload.model_id not in {m["id"] for m in store.models()}:
        raise HTTPException(400, "Model is not in the local catalog")
    experiment = {"id": store.new_id("exp"), "name": payload.name, "model_id": payload.model_id, "dataset_id": payload.dataset_id, "status": "queued", "progress": 0, "created_at": datetime.now(timezone.utc).isoformat(), "config": payload.config.model_dump()}
    return store.add_experiment(experiment)


def _run_training(experiment_id: str) -> None:
    experiment = store.get_experiment(experiment_id)
    if not experiment:
        return
    store.update_experiment(experiment_id, status="running", progress=1)
    dataset = store.get_dataset(experiment["dataset_id"])
    try:
        rows, _ = load_and_validate(Path(dataset["path"]), dataset["name"])
        def update(progress: int, info: dict) -> None:
            store.update_experiment(experiment_id, progress=progress, phase=info.get("phase"), message=info.get("message"))
        metrics = train_with_lora(model_id=experiment["model_id"], rows=rows, config=experiment["config"], experiment_id=experiment_id, on_progress=update)
        store.update_experiment(experiment_id, status="completed", progress=100, metrics=metrics, artifact_dir=metrics.get("artifact_dir"))
    except Exception as exc:
        store.update_experiment(experiment_id, status="failed", progress=0, error=str(exc))


@router.post("/experiments/{experiment_id}/train")
def start_training(experiment_id: str, background_tasks: BackgroundTasks) -> dict:
    experiment = store.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(404, "Experiment not found")
    if experiment["status"] == "running":
        return experiment
    background_tasks.add_task(_run_training, experiment_id)
    return store.update_experiment(experiment_id, status="queued", progress=0) or experiment
