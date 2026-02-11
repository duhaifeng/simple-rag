<template>
  <div class="page">
    <h2>召回测试台</h2>
    <div class="query-form">
      <textarea v-model="queryText" placeholder="输入 Query..." rows="3" />
      <button @click="doQuery" :disabled="loading">检索</button>
    </div>
    <div v-if="loading" class="loading">检索中…</div>
    <div v-if="results.length" class="results">
      <h3>结果（{{ results.length }} 条）</h3>
      <div v-for="r in results" :key="r.chunk_id" class="result-card">
        <div class="meta">
          <span class="rank">#{{ r.rank }}</span>
          <span class="score">{{ r.score.toFixed(4) }}</span>
          <span class="source">{{ r.source }}</span>
        </div>
        <p class="text">{{ r.text }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { postQuery, type ChunkResult } from '../api/query'

const queryText = ref('')
const results = ref<ChunkResult[]>([])
const loading = ref(false)

async function doQuery() {
  if (!queryText.value.trim()) return
  loading.value = true
  try {
    const resp = await postQuery({ query: queryText.value })
    results.value = resp.data.results
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page { max-width: 900px; margin: 0 auto; padding: 24px; }
.query-form { display: flex; gap: 12px; align-items: flex-start; }
.query-form textarea { flex: 1; padding: 8px; font-size: 14px; border: 1px solid #ccc; border-radius: 6px; }
.query-form button { padding: 10px 24px; font-size: 14px; border: none; border-radius: 6px; background: #409eff; color: #fff; cursor: pointer; }
.query-form button:disabled { opacity: 0.5; }
.loading { margin-top: 16px; color: #666; }
.results { margin-top: 24px; }
.result-card { border: 1px solid #eee; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
.meta { display: flex; gap: 12px; font-size: 12px; color: #999; margin-bottom: 6px; }
.rank { font-weight: bold; color: #333; }
.score { color: #409eff; }
.text { font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
</style>
