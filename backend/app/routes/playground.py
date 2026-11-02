from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.storage import resolve_model_source, store

router = APIRouter(tags=["playground"])


class GenerateRequest(BaseModel):
    model: str = Field(pattern="^(original|finetuned)$")
    experiment_id: str | None = None
    prompt: str = Field(min_length=1, max_length=8000)
    temperature: float = Field(.7, ge=0, le=2)
    max_tokens: int = Field(180, ge=1, le=1024)


@router.post("/playground/generate")
def generate(payload: GenerateRequest) -> dict:
    experiment = store.get_experiment(payload.experiment_id) if payload.experiment_id else None
    if payload.model == "finetuned" and (not experiment or experiment.get("status") != "completed"):
        raise HTTPException(400, "Select a completed experiment before using the fine-tuned model")
    model_id = experiment["model_id"] if payload.model == "finetuned" and experiment else "google/flan-t5-small"
    adapter_path = experiment.get("artifact_dir") if experiment else None
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer
        model_source, local_only = resolve_model_source(model_id)
        if not local_only:
            raise RuntimeError(f"Local model files are missing for {model_id}. Choose the local FLAN-T5 model or run the setup download once.")
        is_seq2seq = "t5" in model_id.lower()
        tokenizer = AutoTokenizer.from_pretrained(adapter_path or model_source, local_files_only=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        base = (AutoModelForSeq2SeqLM if is_seq2seq else AutoModelForCausalLM).from_pretrained(model_source, local_files_only=True)
        model = PeftModel.from_pretrained(base, adapter_path) if adapter_path and payload.model == "finetuned" else base
        tokens = tokenizer(payload.prompt, return_tensors="pt", truncation=True)
        with torch.no_grad():
            output = model.generate(**tokens, max_new_tokens=payload.max_tokens, temperature=max(payload.temperature, .01), do_sample=payload.temperature > 0, repetition_penalty=1.05, pad_token_id=tokenizer.eos_token_id)
        if is_seq2seq:
            generated = tokenizer.decode(output[0], skip_special_tokens=True).strip()
            generated_tokens = int(output.shape[-1])
        else:
            start = tokens["input_ids"].shape[-1]
            generated = tokenizer.decode(output[0][start:], skip_special_tokens=True).strip()
            generated_tokens = max(0, int(output.shape[-1] - start))
        return {"response": generated, "model": model_id, "generated_tokens": generated_tokens}
    except ImportError as exc:
        raise HTTPException(503, "Inference dependencies are not installed. Run: pip install -r backend/requirements.txt") from exc
    except Exception as exc:
        raise HTTPException(500, f"Model inference failed: {exc}") from exc
