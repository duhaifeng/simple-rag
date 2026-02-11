import apiClient from './client'

export interface QueryRequest {
  query: string
  retrieval_profile?: string
  rerank_profile?: string
  top_k?: number
  top_n?: number
  filters?: Record<string, unknown>
}

export interface ChunkResult {
  chunk_id: string
  doc_id: string
  text: string
  score: number
  rank: number
  source?: string
  metadata?: Record<string, unknown>
}

export interface QueryResponse {
  query: string
  rewritten_query?: string
  results: ChunkResult[]
  debug?: Record<string, unknown>
}

export function postQuery(req: QueryRequest) {
  return apiClient.post<QueryResponse>('/query', req)
}
