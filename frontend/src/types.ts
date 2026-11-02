export type View = 'overview' | 'datasets' | 'training' | 'playground' | 'history'

export type Dataset = {
  id: string
  name: string
  format: 'JSONL' | 'CSV'
  records: number
  status: 'Ready' | 'Needs review' | 'Processing'
  created_at: string
  samples: { instruction: string; response: string }[]
}

export type Experiment = {
  id: string
  name: string
  model_id: string
  dataset_id: string
  status: 'completed' | 'running' | 'failed' | 'queued'
  progress: number
  created_at: string
  metrics?: { train_loss?: number; eval_loss?: number; duration_seconds?: number }
  config: { epochs: number; batch_size: number; learning_rate: number; lora_r: number; lora_alpha: number; max_length: number }
}

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
