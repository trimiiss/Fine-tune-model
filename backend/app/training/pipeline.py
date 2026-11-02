from __future__ import annotations

import inspect
import json
import time
from typing import Callable

from app.services.storage import ARTIFACT_DIR, resolve_model_source
from app.utils.dataset import to_training_text


def train_with_lora(*, model_id: str, rows: list[dict[str, str]], config: dict, experiment_id: str, on_progress: Callable[[int, dict], None]) -> dict:
    """Train either a local instruction model (FLAN-T5) or a causal LM adapter with PEFT LoRA."""
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer, DataCollatorForLanguageModeling, DataCollatorForSeq2Seq, Trainer, TrainingArguments
    except ImportError as exc:
        raise RuntimeError("Training dependencies are not installed. Run: pip install -r backend/requirements.txt") from exc

    start = time.perf_counter()
    output_dir = ARTIFACT_DIR / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    model_source, local_only = resolve_model_source(model_id)
    if not local_only:
        raise RuntimeError(f"Local model files are missing for {model_id}. Choose a model marked local or run the setup download once.")
    is_seq2seq = "t5" in model_id.lower()
    on_progress(5, {"phase": "loading_model", "message": f"Loading local model {model_source}"})
    tokenizer = AutoTokenizer.from_pretrained(model_source, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = (AutoModelForSeq2SeqLM if is_seq2seq else AutoModelForCausalLM).from_pretrained(model_source, local_files_only=True)

    if is_seq2seq:
        lora = LoraConfig(task_type=TaskType.SEQ_2_SEQ_LM, r=int(config["lora_r"]), lora_alpha=int(config["lora_alpha"]), lora_dropout=0.05, target_modules=["q", "v"], bias="none")
        dataset = Dataset.from_list(rows)

        def tokenize(batch: dict) -> dict:
            inputs = tokenizer(batch["instruction"], truncation=True, max_length=int(config["max_length"]))
            labels = tokenizer(text_target=batch["response"], truncation=True, max_length=int(config["max_length"]))
            inputs["labels"] = labels["input_ids"]
            return inputs

        tokenized = dataset.map(tokenize, batched=True, remove_columns=["instruction", "response"])
        collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)
    else:
        lora = LoraConfig(task_type=TaskType.CAUSAL_LM, r=int(config["lora_r"]), lora_alpha=int(config["lora_alpha"]), lora_dropout=0.05, target_modules=["c_attn"] if "gpt2" in model_id.lower() else None, bias="none")
        dataset = Dataset.from_list([{"text": to_training_text(row)} for row in rows])

        def tokenize(batch: dict) -> dict:
            return tokenizer(batch["text"], truncation=True, max_length=int(config["max_length"]), padding="max_length")

        tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])
        collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    model = get_peft_model(model, lora)
    eval_size = max(1, min(len(tokenized) // 5, 32)) if len(tokenized) > 4 else 0
    train_dataset = tokenized.select(range(len(tokenized) - eval_size)) if eval_size else tokenized
    eval_dataset = tokenized.select(range(len(tokenized) - eval_size, len(tokenized))) if eval_size else None
    training_kwargs = {"output_dir": str(output_dir), "num_train_epochs": float(config["epochs"]), "per_device_train_batch_size": int(config["batch_size"]), "learning_rate": float(config["learning_rate"]), "logging_steps": 1, "save_strategy": "epoch", "report_to": [], "fp16": bool(torch.cuda.is_available()), "remove_unused_columns": False}
    strategy_key = "eval_strategy" if "eval_strategy" in inspect.signature(TrainingArguments).parameters else "evaluation_strategy"
    training_kwargs[strategy_key] = "epoch" if eval_dataset else "no"
    args = TrainingArguments(**training_kwargs)
    trainer_kwargs = {"model": model, "args": args, "train_dataset": train_dataset, "eval_dataset": eval_dataset, "data_collator": collator}
    trainer_key = "processing_class" if "processing_class" in inspect.signature(Trainer).parameters else "tokenizer"
    trainer_kwargs[trainer_key] = tokenizer
    trainer = Trainer(**trainer_kwargs)
    on_progress(15, {"phase": "training", "message": "Training instruction adapter weights"})
    result = trainer.train()
    on_progress(90, {"phase": "saving", "message": "Saving adapter and tokenizer"})
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    metrics = dict(result.metrics)
    if eval_dataset:
        for key, value in trainer.evaluate().items():
            if isinstance(value, (int, float)):
                metrics[key if key.startswith("eval_") else f"eval_{key}"] = value
    metrics["duration_seconds"] = round(time.perf_counter() - start, 2)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    on_progress(100, {"phase": "completed", "message": "Training completed"})
    return {"train_loss": metrics.get("train_loss"), "eval_loss": metrics.get("eval_loss"), "duration_seconds": metrics["duration_seconds"], "artifact_dir": str(output_dir)}
