import axios from 'axios';
import { IngestResponse } from '../types';

const api = axios.create({ baseURL: '/api' });

export async function uploadFile(
  file: File,
  sourceType?: string
): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (sourceType) {
    formData.append('source_type', sourceType);
  }

  const response = await api.post<IngestResponse>('/ingest/file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function ingestRepo(repoUrl: string): Promise<IngestResponse> {
  const response = await api.post<IngestResponse>('/ingest/repo', {
    repo_url: repoUrl,
  });
  return response.data;
}

export async function ingestText(
  text: string,
  filename: string,
  sourceType: string
): Promise<IngestResponse> {
  const response = await api.post<IngestResponse>('/ingest/text', {
    text,
    filename,
    source_type: sourceType,
  });
  return response.data;
}
