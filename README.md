# Fine-Tuning Studio

Fine-Tuning Studio is a local-first portfolio app for learning the workflow of adapting a small language model. It combines a React + Vite + TypeScript + Tailwind dashboard with FastAPI, real Transformers / PEFT LoRA training, local artifact storage, and a model playground.

## Windows setup

Open two PowerShell terminals from the repository root.

### Backend

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
python backend\run.py
```

The API is at `http://127.0.0.1:8000` and the docs are at `/docs`. This repository includes the small `sshleifer/tiny-gpt2` checkpoint in `backend/models/sshleifer--tiny-gpt2`, so training and inference run offline after installation. CPU is supported but slower than CUDA.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Dataset format

JSONL rows and CSV files must contain `instruction` and `response` fields:

```json
{"instruction":"Explain machine learning simply.","response":"Machine learning lets computers learn patterns from examples."}
```

The API rejects malformed, empty, or incomplete datasets before saving them.

## Verification

```powershell
python -c "import sys; sys.path.insert(0, 'backend'); from app.main import app; print(app.title, len(app.routes))"
cd frontend
npm run build
```

## Project map

```text
frontend/              React dashboard
backend/app/main.py    FastAPI entry point
backend/app/routes/    Dataset, experiment, playground APIs
backend/app/training/  Transformers + PEFT LoRA pipeline
backend/data/          Uploaded datasets
backend/artifacts/     Adapter checkpoints and metrics
```

This is a local educational studio, not a multi-user production service. There is no authentication, durable queue worker, or remote object storage. Training uses FastAPI background tasks and requires the API process to remain open.
