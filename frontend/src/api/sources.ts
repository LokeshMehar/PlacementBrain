import axios from 'axios';
import { SourceItem } from '../types';

const api = axios.create({ baseURL: '/api' });

export async function getSources(): Promise<SourceItem[]> {
  const response = await api.get<SourceItem[]>('/sources');
  return response.data;
}

export async function deleteSource(sourceId: string): Promise<void> {
  await api.delete(`/sources/${sourceId}`);
}
