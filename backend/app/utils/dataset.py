from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


class DatasetValidationError(ValueError):
    pass


def load_and_validate(path: Path, original_name: str) -> tuple[list[dict[str, str]], str]:
    suffix = path.suffix.lower()
    if suffix not in {".jsonl", ".csv"}:
        raise DatasetValidationError("Only .jsonl and .csv files are supported")
    try:
        if suffix == ".jsonl":
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        else:
            rows = pd.read_csv(path).fillna("").to_dict(orient="records")
    except Exception as exc:
        raise DatasetValidationError(f"Could not parse {original_name}: {exc}") from exc
    if not rows:
        raise DatasetValidationError("The dataset is empty")
    normalized: list[dict[str, str]] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict) or "instruction" not in row or "response" not in row:
            raise DatasetValidationError(f"Row {index} must contain instruction and response fields")
        instruction, response = str(row["instruction"]).strip(), str(row["response"]).strip()
        if not instruction or not response:
            raise DatasetValidationError(f"Row {index} has an empty instruction or response")
        normalized.append({"instruction": instruction, "response": response})
    return normalized, "JSONL" if suffix == ".jsonl" else "CSV"


def to_training_text(row: dict[str, str]) -> str:
    return f"### Instruction:\n{row['instruction']}\n\n### Response:\n{row['response']}"
