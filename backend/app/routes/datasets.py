from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.storage import DATA_DIR, store
from app.utils.dataset import DatasetValidationError, load_and_validate

router = APIRouter(tags=["datasets"])


@router.get("/datasets")
def list_datasets() -> list[dict]:
    return store.list_datasets()


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str) -> dict:
    dataset = store.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    return dataset


@router.post("/datasets/upload")
def upload_dataset(file: UploadFile = File(...)) -> dict:
    name = file.filename or "dataset"
    suffix = Path(name).suffix.lower()
    if suffix not in {".jsonl", ".csv"}:
        raise HTTPException(400, "Upload a .jsonl or .csv file")
    dataset_id = store.new_id("ds")
    saved_path = DATA_DIR / f"{dataset_id}{suffix}"
    try:
        with saved_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        rows, fmt = load_and_validate(saved_path, name)
    except DatasetValidationError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from exc
    dataset = {"id": dataset_id, "name": name, "format": fmt, "records": len(rows), "status": "Ready", "created_at": datetime.now(timezone.utc).isoformat(), "samples": rows[:5], "path": str(saved_path)}
    return store.add_dataset(dataset)


@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: str) -> dict:
    dataset = store.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    Path(dataset.get("path", "")).unlink(missing_ok=True)
    store.delete_dataset(dataset_id)
    return {"ok": True}
