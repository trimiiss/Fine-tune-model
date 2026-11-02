from __future__ import annotations

import json
import platform
import threading
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
ARTIFACT_DIR = ROOT / "artifacts"
MODEL_DIR = ROOT / "models"
DB_PATH = ROOT / "studio.json"
DATA_DIR.mkdir(exist_ok=True)
ARTIFACT_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

MODEL_CATALOG = [
    {"id": "google/flan-t5-small", "name": "FLAN-T5 Small", "family": "Instruction Seq2Seq", "size": "308 MB", "description": "An instruction-tuned model that produces useful answers for prompts and small educational datasets.", "recommended": True},
    {"id": "sshleifer/tiny-gpt2", "name": "Tiny GPT-2", "family": "Causal LM", "size": "2.5 MB", "description": "A tiny smoke-test checkpoint. Fast, but not suitable for coherent chatbot responses."},
    {"id": "distilgpt2", "name": "DistilGPT-2", "family": "Causal LM", "size": "328 MB", "description": "A compact GPT-2 variant with a useful quality / hardware trade-off."},
    {"id": "gpt2", "name": "GPT-2", "family": "Causal LM", "size": "548 MB", "description": "The classic small language model; expect more memory and longer CPU runs."},
]


class StudioStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._db: dict[str, Any] = {"datasets": {}, "experiments": {}}
        self._load()

    def _load(self) -> None:
        if DB_PATH.exists():
            try:
                self._db.update(json.loads(DB_PATH.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass

    def _save(self) -> None:
        DB_PATH.write_text(json.dumps(self._db, indent=2), encoding="utf-8")

    def runtime_summary(self) -> dict[str, str]:
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
        return {"platform": platform.system(), "python": platform.python_version(), "device": device}

    def models(self) -> list[dict]:
        result = []
        for model in MODEL_CATALOG:
            local_path = MODEL_DIR / model["id"].replace("/", "--")
            result.append({**model, "local_available": (local_path / "config.json").exists(), "local_path": str(local_path)})
        return result

    def list_datasets(self) -> list[dict]:
        return sorted(self._db["datasets"].values(), key=lambda x: x["created_at"], reverse=True)

    def get_dataset(self, dataset_id: str) -> dict | None:
        return self._db["datasets"].get(dataset_id)

    def add_dataset(self, dataset: dict) -> dict:
        with self._lock:
            self._db["datasets"][dataset["id"]] = dataset
            self._save()
            return dataset

    def delete_dataset(self, dataset_id: str) -> bool:
        with self._lock:
            existed = self._db["datasets"].pop(dataset_id, None) is not None
            if existed:
                self._save()
            return existed

    def list_experiments(self) -> list[dict]:
        return sorted(self._db["experiments"].values(), key=lambda x: x["created_at"], reverse=True)

    def get_experiment(self, experiment_id: str) -> dict | None:
        return self._db["experiments"].get(experiment_id)

    def add_experiment(self, experiment: dict) -> dict:
        with self._lock:
            self._db["experiments"][experiment["id"]] = experiment
            self._save()
            return experiment

    def update_experiment(self, experiment_id: str, **updates: Any) -> dict | None:
        with self._lock:
            experiment = self._db["experiments"].get(experiment_id)
            if not experiment:
                return None
            experiment.update(updates)
            self._save()
            return experiment

    def dashboard(self) -> dict:
        experiments = self.list_experiments()
        return {"experiments": len(experiments), "datasets": len(self._db["datasets"]), "completed": sum(e["status"] == "completed" for e in experiments), "running": sum(e["status"] in {"running", "queued"} for e in experiments), "total_records": sum(d["records"] for d in self._db["datasets"].values()), "recent": experiments[:5]}

    @staticmethod
    def new_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"


store = StudioStore()


def resolve_model_source(model_id: str) -> tuple[str, bool]:
    """Return the local checkpoint when it exists; never require Hub access for it."""
    local_path = MODEL_DIR / model_id.replace("/", "--")
    if (local_path / "config.json").exists():
        return str(local_path), True
    return model_id, False
