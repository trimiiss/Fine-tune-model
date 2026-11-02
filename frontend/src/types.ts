export type View = 'overview' | 'datasets' | 'training' | 'playground' | 'history' | 'models'

export type DatasetQuality = {
  score: number
  duplicates: number
  long_examples: number
  short_examples: number
  avg_instruction_words: number
  avg_response_words: number
  estimated_words: number
  issues: string[]
}

export type Dataset = {
  id: string
  name: string
  format: 'JSONL' | 'CSV'
  records: number
  status: 'Ready' | 'Needs review' | 'Processing'
  created_at: string
  samples: { instruction: string; response: string }[]
  quality?: DatasetQuality
}

export type Experiment = {
  id: string
  name: string
  model_id: string
  dataset_id: string
  status: 'completed' | 'running' | 'failed' | 'queued' | 'cancelling' | 'cancelled'
  progress: number
  created_at: string
  metrics?: { train_loss?: number; eval_loss?: number; duration_seconds?: number; history?: MetricPoint[]; checkpoints?: string[]; artifact_dir?: string }
  config: { epochs: number; batch_size: number; learning_rate: number; lora_r: number; lora_alpha: number; max_length: number; seed?: number }
  phase?: string
  message?: string
  error?: string
  logs?: TrainingLog[]
}

export type MetricPoint = { step?: number; loss?: number; eval_loss?: number; learning_rate?: number; epoch?: number }
export type TrainingLog = { at: string; progress: number; phase?: string; message: string }

export type ModelOption = {
  id: string
  name: string
  family: string
  size: string
  description: string
  recommended?: boolean
  local_only?: boolean
  local_available?: boolean
  local_path?: string
}
