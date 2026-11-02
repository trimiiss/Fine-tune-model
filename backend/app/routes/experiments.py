from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.services.storage import store
from app.training.pipeline import TrainingCancelled, train_with_lora
from app.utils.dataset import load_and_validate

router = APIRouter(tags=["experiments"])


class TrainingConfig(BaseModel):
    epochs: int = Field(3, ge=1, le=20)
    batch_size: int = Field(4, ge=1, le=64)
    learning_rate: float = Field(2e-4, gt=0, le=1)
    lora_r: int = Field(16, ge=1, le=256)
    lora_alpha: int = Field(32, ge=1, le=512)
    max_length: int = Field(512, ge=32, le=4096)
    seed: int = Field(42, ge=0, le=2_147_483_647)


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    dataset_id: str
    model_id: str
    config: TrainingConfig


_cancel_events: dict[str, threading.Event] = {}
_cancel_lock = threading.Lock()


def _event_for(experiment_id: str) -> threading.Event:
    with _cancel_lock:
        return _cancel_events.setdefault(experiment_id, threading.Event())


def _queue_training(experiment_id: str, background_tasks: BackgroundTasks) -> dict:
    event = _event_for(experiment_id)
    event.clear()
    background_tasks.add_task(_run_training, experiment_id)
    return store.update_experiment(experiment_id, status="queued", progress=0, error=None, cancel_requested=False) or {}


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
    experiment = {"id": store.new_id("exp"), "name": payload.name, "model_id": payload.model_id, "dataset_id": payload.dataset_id, "status": "queued", "progress": 0, "created_at": datetime.now(timezone.utc).isoformat(), "config": payload.config.model_dump(), "logs": []}
    return store.add_experiment(experiment)


def _run_training(experiment_id: str) -> None:
    experiment = store.get_experiment(experiment_id)
    if not experiment:
        return
    event = _event_for(experiment_id)
    if event.is_set():
        store.update_experiment(experiment_id, status="cancelled", message="Training cancelled before it started")
        return
    store.update_experiment(experiment_id, status="running", progress=1, phase="starting", message="Preparing local training run")
    dataset = store.get_dataset(experiment["dataset_id"])
    try:
        if not dataset:
            raise RuntimeError("The dataset for this experiment no longer exists")
        rows, _ = load_and_validate(Path(dataset["path"]), dataset["name"])
        def update(progress: int, info: dict) -> None:
            message = info.get("message", "Training update")
            store.update_experiment(experiment_id, progress=progress, phase=info.get("phase"), message=message)
            store.append_experiment_log(experiment_id, {"at": datetime.now(timezone.utc).isoformat(), "progress": progress, "phase": info.get("phase"), "message": message})
        metrics = train_with_lora(model_id=experiment["model_id"], rows=rows, config=experiment["config"], experiment_id=experiment_id, on_progress=update, should_stop=event.is_set)
        store.update_experiment(experiment_id, status="completed", progress=100, metrics=metrics, artifact_dir=metrics.get("artifact_dir"), phase="completed", message="Training completed")
    except TrainingCancelled as exc:
        store.update_experiment(experiment_id, status="cancelled", message=str(exc), phase="cancelled")
        store.append_experiment_log(experiment_id, {"at": datetime.now(timezone.utc).isoformat(), "progress": store.get_experiment(experiment_id).get("progress", 0), "phase": "cancelled", "message": str(exc)})
    except Exception as exc:
        store.update_experiment(experiment_id, status="failed", error=str(exc), phase="failed", message="Training failed")
        store.append_experiment_log(experiment_id, {"at": datetime.now(timezone.utc).isoformat(), "progress": store.get_experiment(experiment_id).get("progress", 0), "phase": "failed", "message": str(exc)})
    finally:
        with _cancel_lock:
            _cancel_events.pop(experiment_id, None)


@router.post("/experiments/{experiment_id}/train")
def start_training(experiment_id: str, background_tasks: BackgroundTasks) -> dict:
    experiment = store.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(404, "Experiment not found")
    if experiment["status"] in {"running", "queued", "cancelling"}:
        return experiment
    if experiment["status"] == "completed":
        raise HTTPException(409, "This experiment is already completed. Use retry to start it again.")
    _event_for(experiment_id)
    return _queue_training(experiment_id, background_tasks) or experiment


@router.post("/experiments/{experiment_id}/cancel")
def cancel_training(experiment_id: str) -> dict:
    experiment = store.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(404, "Experiment not found")
    if experiment["status"] in {"completed", "failed", "cancelled"}:
        return experiment
    _event_for(experiment_id).set()
    return store.update_experiment(experiment_id, status="cancelling", cancel_requested=True, message="Cancellation requested") or experiment


@router.post("/experiments/{experiment_id}/retry")
def retry_training(experiment_id: str, background_tasks: BackgroundTasks) -> dict:
    experiment = store.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(404, "Experiment not found")
    if experiment["status"] in {"running", "queued", "cancelling"}:
        raise HTTPException(409, "This experiment is already running")
    if not store.get_dataset(experiment["dataset_id"]):
        raise HTTPException(404, "Dataset not found")
    experiment = store.update_experiment(experiment_id, status="queued", progress=0, metrics=None, error=None, logs=[], phase="queued", message="Retry queued", artifact_dir=None, cancel_requested=False) or experiment
    return _queue_training(experiment_id, background_tasks) or experiment
