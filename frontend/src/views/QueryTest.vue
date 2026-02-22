<template>
  <div class="page">
    <h2>召回测试台</h2>
    <p class="desc">输入查询语句，测试检索效果。</p>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="options">
      <label class="opt-label">召回模式</label>
      <select v-model="retrievalProfile" class="opt-select" :disabled="loading">
        <option value="sparse_only">Sparse（BM25）</option>
        <option value="hybrid_default">Hybrid（Dense + BM25）</option>
        <option value="dense_only">Dense（向量）</option>
      </select>
    </div>

    <div class="query-form">
      <textarea v-model="queryText" placeholder="输入 Query..." rows="3"></textarea>
      <button @click="doQuery" :disabled="loading">检索</button>
    </div>

    <div v-if="loading" class="loading">检索中…</div>

    <div v-if="searched && !loading" class="results">
      <h3>结果（{{ results.length }} 条）</h3>
      <div v-if="!results.length" class="empty-hint">
        没有命中任何 chunk。请确认已上传并解析文档，且查询词在文档内容中出现过。
      </div>
      <div v-for="r in results" :key="r.chunk_id" class="result-card">
        <div class="meta">
          <span class="rank">#{{ r.rank }}</span>
          <span class="score">{{ r.score.toFixed(4) }}</span>
          <span class="source">{{ r.source }}</span>
        </div>
        <p class="text">{{ r.text }}</p>
      </div>
    </div>

    <details v-if="debug" class="debug" :open="results.length === 0">
      <summary>调试信息</summary>
      <pre>{{ debug }}</pre>
    </details>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { postQuery, type ChunkResult } from '../api/query'

const queryText = ref('')
const results = ref<ChunkResult[]>([])
const loading = ref(false)
const error = ref('')
const searched = ref(false)
const debug = ref<Record<string, unknown> | null>(null)
const retrievalProfile = ref<'hybrid_default' | 'dense_only' | 'sparse_only'>('sparse_only')

async function doQuery() {
  if (!queryText.value.trim()) return
  loading.value = true
  error.value = ''
  searched.value = true
  try {
    const resp = await postQuery({ query: queryText.value, retrieval_profile: retrievalProfile.value })
    results.value = resp.data.results
    debug.value = (resp.data as any).debug || null
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '检索失败'
    debug.value = null
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page {
  max-width: 960px;
  margin: 24px auto;
  padding: 28px 32px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  box-shadow: 0 8px 22px rgba(2, 6, 23, 0.06);
}

.desc {
  color: #475569;
  margin-bottom: 24px;
}

.error-banner {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 14px;
  margin-bottom: 16px;
}

.query-form {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.options {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.opt-label {
  font-size: 12px;
  color: #475569;
  font-weight: 600;
}
.opt-select {
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #1e293b;
  font-size: 13px;
}
.opt-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.query-form textarea {
  flex: 1;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #1e293b;
  resize: vertical;
  transition: border-color 0.15s;
}
.query-form textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.query-form button {
  padding: 10px 28px;
  white-space: nowrap;
}

.loading {
  margin-top: 20px;
  color: #475569;
  font-size: 14px;
}

.results {
  margin-top: 28px;
}

.results h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 16px;
}

.empty-hint {
  background: #fff;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  padding: 14px 16px;
  color: #64748b;
  font-size: 13px;
  margin-bottom: 12px;
}

.result-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 12px;
  background: #fff;
  transition: box-shadow 0.15s;
}
.result-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.meta {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
}
.rank {
  font-weight: 700;
  color: #1e293b;
}
.score {
  color: #3b82f6;
  font-weight: 600;
}

.text {
  font-size: 14px;
  line-height: 1.7;
  color: #334155;
  white-space: pre-wrap;
  margin: 0;
}

.debug {
  margin-top: 18px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 12px;
}
.debug summary {
  cursor: pointer;
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
}
.debug pre {
  margin: 10px 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: #334155;
  font-size: 12px;
}
</style>
