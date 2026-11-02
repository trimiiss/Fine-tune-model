# Fine-Tuning Studio

Fine-Tuning Studio is a local-first workspace for learning and demonstrating the full lifecycle of a small language-model fine-tune:

1. Upload and validate an instruction dataset.
2. Configure a PEFT/LoRA experiment.
3. Train an adapter locally with Transformers.
4. Track progress, metrics, and artifacts.
5. Compare the base model with the fine-tuned adapter in the playground.

The project combines a React dashboard with a FastAPI service. It is designed for experimentation, demos, and portfolio work—not as a production multi-user training platform.

## Highlights

- React + Vite + TypeScript + Tailwind dashboard
- FastAPI backend with interactive OpenAPI docs
- JSONL and CSV dataset upload with validation
- Local Transformers and PEFT LoRA training
- CPU support, with CUDA used automatically when available
- Base-model and fine-tuned-model playground
- Local experiment history, metrics, datasets, and adapter checkpoints
- Offline-friendly local model loading when checkpoint files are present

## Stack

| Area | Technology |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| API | FastAPI, Uvicorn, Pydantic |
| ML | PyTorch, Transformers, Datasets, PEFT/LoRA, Accelerate |
| Storage | Local JSON metadata, local dataset files, local artifacts |

## Requirements

- Windows PowerShell instructions are shown below; macOS/Linux work with equivalent commands.
- Python 3.11 or 3.12 recommended
- Node.js 18+ and npm
- About 2–4 GB of disk space for the Python environment and local model files
- CPU works for small experiments; CUDA is recommended for faster training

## Quick start on Windows

Open two PowerShell terminals from the repository root.

### 1. Start the backend

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
python backend\run.py
```

The API runs at `http://127.0.0.1:8000`.

- Health check: `http://127.0.0.1:8000/api/health`
- API documentation: `http://127.0.0.1:8000/docs`

If PowerShell blocks activation, run this once in an elevated PowerShell window or use the venv's Python directly:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173` in your browser.

The frontend uses `http://127.0.0.1:8000/api` by default. To point it at another API URL, create `frontend/.env.local`:

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

## First experiment

1. Open **Dataset workspace** and upload a `.jsonl` or `.csv` file.
2. Open **Fine-tune a model** and choose the dataset and a locally available model.
3. Keep the default LoRA settings for a first run.
4. Start training and watch the status update.
5. Open **Model playground** and compare the base model with a completed adapter.

Training runs in a FastAPI background task. Keep the backend terminal open until the run finishes.

## Dataset format

Every row must contain non-empty `instruction` and `response` fields.

JSONL example:

```json
{"instruction":"Explain machine learning simply.","response":"Machine learning lets computers learn patterns from examples."}
{"instruction":"What is LoRA?","response":"LoRA trains a small adapter instead of changing every weight in the base model."}
```

CSV example:

```csv
instruction,response
Explain machine learning simply.,Machine learning lets computers learn patterns from examples.
What is LoRA?,LoRA trains a small adapter instead of changing every weight in the base model.
```

Uploads are parsed and validated before they are added to the dataset library. Empty files, malformed rows, and missing columns are rejected.

## Local models

The model catalog contains:

- `google/flan-t5-small` — recommended instruction/response model
- `sshleifer/tiny-gpt2` — very small smoke-test model
- `distilgpt2` — catalog entry; checkpoint must be added locally before use
- `gpt2` — catalog entry; checkpoint must be added locally before use

The repository includes local files for FLAN-T5 Small and Tiny GPT-2 under `backend/models/`. The application intentionally uses `local_files_only=True`, so training and inference do not silently download model files. A model must have its checkpoint files in:

```text
backend/models/<owner>--<model-name>/
```

For example, `google/flan-t5-small` maps to `backend/models/google--flan-t5-small/`.

## Project structure

```text
frontend/
  src/App.tsx                 Dashboard views and experiment workflow
  src/components/             Reusable UI components
  src/lib/api.ts              Typed frontend API client

backend/
  run.py                      Local Uvicorn launcher
  app/main.py                 FastAPI application and top-level endpoints
  app/routes/                 Dataset, experiment, and playground APIs
  app/training/pipeline.py    Transformers + PEFT LoRA training pipeline
  app/utils/dataset.py        JSONL/CSV parsing and validation
  app/services/storage.py     Local metadata and model catalog
  data/                       Uploaded datasets and sample data
  models/                     Local model checkpoints
  artifacts/                  Generated adapters and metrics
```

Runtime data is intentionally local and ignored by Git:

- `backend/studio.json` stores experiment and dataset metadata.
- `backend/data/` stores uploaded datasets.
- `backend/artifacts/` stores adapter checkpoints and `metrics.json` files.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Check API status and runtime device |
| `GET` | `/api/models` | List catalogued models and local availability |
| `GET` | `/api/dashboard` | Return dashboard counts and recent experiments |
| `GET/POST/DELETE` | `/api/datasets` | List, upload, and delete datasets |
| `GET/POST` | `/api/experiments` | List and create experiments |
| `POST` | `/api/experiments/{id}/train` | Start a background training run |
| `POST` | `/api/playground/generate` | Generate text from a base or fine-tuned model |

The complete request and response schemas are available at `/docs` while the backend is running.

## Verification

Backend import check:

```powershell
python -c "import sys; sys.path.insert(0, 'backend'); from app.main import app; print(app.title, len(app.routes))"
```

Frontend production build:

```powershell
cd frontend
npm run build
```

## Troubleshooting

### The frontend says “API offline”

Make sure the backend terminal is still running and that the API responds at `http://127.0.0.1:8000/api/health`. If you changed the API port or host, update `VITE_API_URL` and restart Vite.

### A model is listed but training fails

Only models with local checkpoint files can train. Check the model's `local_available` value from `/api/models` and place the required files under the matching `backend/models/` directory.

### Training is slow

Use Tiny GPT-2 for a smoke test, reduce epochs and max sequence length, or run with a CUDA-enabled PyTorch installation. CPU training is expected to be slow.

### The fine-tuned model cannot be selected

The playground only enables the adapter after its experiment reaches `completed`. Failed or queued experiments cannot be used for inference.

## What to improve next

Recommended order for turning this into a stronger project:

1. **Add automated tests.** Cover dataset validation, API routes, experiment state transitions, and a mocked training run.
2. **Improve experiment evaluation.** Store a held-out validation set, show real loss curves from `metrics.json`, and add a small side-by-side evaluation table.
3. **Make training safer.** Add cancellation, prevent duplicate runs, validate available disk/RAM, and persist logs separately from metadata.
4. **Add model management.** Provide a clear download/import flow and hide models that are not locally available.
5. **Improve reproducibility.** Save the dataset hash, library versions, device, random seed, model revision, and full training configuration with every run.
6. **Polish the UI.** Add experiment detail pages, artifact download buttons, error details, empty/loading states, and a real progress timeline.
7. **Prepare deployment.** Add Docker support, environment-based CORS configuration, a real database, a worker queue, authentication, and object storage.
8. **Add project quality gates.** Use Ruff/Black/Pytest for Python, ESLint/Prettier/Vitest for TypeScript, and GitHub Actions for build and test checks.

## Current limitations

- Local single-process application; no authentication or multi-user isolation
- Training uses FastAPI background tasks rather than a durable job queue
- Metadata is stored in a local JSON file
- Uploaded data and generated artifacts are not synced or backed up automatically
- Evaluation and dashboard loss data should be connected to real completed-run metrics

## License

Add a license before publishing this project for reuse. MIT is a reasonable default for a personal educational application, provided any model licenses and dataset licenses are also respected.
