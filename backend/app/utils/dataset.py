from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


class DatasetValidationError(ValueError):
    pass


def quality_report(rows: list[dict[str, str]], max_length: int = 512) -> dict:
    """Return lightweight, model-agnostic quality signals for the dataset UI."""
    normalized = [
        f"{row['instruction'].strip().lower()}\n{row['response'].strip().lower()}"
        for row in rows
    ]
    duplicate_count = len(normalized) - len(set(normalized))
    instruction_lengths = [len(row["instruction"].split()) for row in rows]
    response_lengths = [len(row["response"].split()) for row in rows]
    total_lengths = [a + b for a, b in zip(instruction_lengths, response_lengths)]
    long_examples = sum(length > max_length for length in total_lengths)
    short_examples = sum(length < 4 for length in total_lengths)
    issues: list[str] = []
    if duplicate_count:
        issues.append(f"{duplicate_count} duplicate example{'s' if duplicate_count != 1 else ''}")
    if long_examples:
        issues.append(f"{long_examples} example{'s' if long_examples != 1 else ''} exceed {max_length} words")
    if short_examples:
        issues.append(f"{short_examples} very short example{'s' if short_examples != 1 else ''}")
    score = max(0, 100 - min(35, duplicate_count * 8) - min(30, long_examples * 4) - min(20, short_examples * 2))
    return {
        "score": score,
        "duplicates": duplicate_count,
        "long_examples": long_examples,
        "short_examples": short_examples,
        "avg_instruction_words": round(sum(instruction_lengths) / len(rows), 1),
        "avg_response_words": round(sum(response_lengths) / len(rows), 1),
        "estimated_words": sum(total_lengths),
        "issues": issues,
    }


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
