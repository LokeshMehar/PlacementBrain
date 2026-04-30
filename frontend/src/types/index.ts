export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
}

export interface Source {
  filename: string;
  source_type: string;
  text: string;
  score: number;
}

export interface SourceItem {
  source_id: string;
  filename: string;
  source_type: string;
  chunk_count: number;
  created_at: string;
}

export interface IngestResponse {
  source_id: string;
  filename: string;
  source_type: string;
  chunk_count: number;
  status: string;
}

export interface UploadStatus {
  filename: string;
  status: 'pending' | 'uploading' | 'done' | 'error';
  progress: number;
  error?: string;
  result?: IngestResponse;
}
