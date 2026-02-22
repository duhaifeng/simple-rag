<template>
  <div class="page">
    <h2>Chunk 预览</h2>
    <p class="desc">查看 chunk 列表、元数据、文本高亮。</p>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="toolbar">
      <label class="label">选择文档</label>
      <select v-model="selectedDocId" class="select" @change="onDocChange" :disabled="loadingDocs">
        <option value="" disabled>{{ loadingDocs ? '加载中…' : '请选择文档' }}</option>
        <option v-for="d in documents" :key="d.doc_id" :value="d.doc_id">
          {{ d.filename }}（{{ statusLabel(d.status) }}）
        </option>
      </select>

      <button class="btn-secondary" @click="refreshChunks" :disabled="!selectedDocId || loadingChunks">
        刷新
      </button>
    </div>

    <div v-if="loadingDocs || loadingChunks" class="loading">加载中…</div>

    <div v-if="!loadingDocs && !documents.length" class="empty-state">
      <div class="icon">🧩</div>
      <p>暂无文档，请先在“文档管理”中上传并解析。</p>
    </div>

    <div v-else-if="selectedDoc && selectedDoc.status !== 'done'" class="hint-banner">
      当前文档状态为 <b>{{ statusLabel(selectedDoc.status) }}</b>，chunk 可能尚未生成；请稍后点击“刷新”。（若失败可去文档管理查看错误信息）
    </div>

    <template v-if="!loadingChunks && selectedDocId">
      <div v-if="chunks.length" class="chunk-list">
        <div class="chunk-header">
          <h3>Chunks（{{ total }} 条）</h3>
          <div class="pager">
            <button class="btn-secondary" @click="prevPage" :disabled="page <= 1 || loadingChunks">上一页</button>
            <span class="page-info">第 {{ page }} 页</span>
            <button class="btn-secondary" @click="nextPage" :disabled="page * pageSize >= total || loadingChunks">
              下一页
            </button>
          </div>
        </div>

        <div v-for="c in chunks" :key="c.chunk_id" class="chunk-card">
          <div class="chunk-meta">
            <span class="chip">#{{ c.chunk_index }}</span>
            <span class="mono">{{ c.chunk_id }}</span>
          </div>
          <pre class="chunk-text">{{ c.text }}</pre>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="icon">🧩</div>
        <p>该文档暂无 chunk（可能为空文档或解析未产出内容）。</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '../api/client'

interface DocItem {
  doc_id: string
  filename: string
  status: string
  error?: string | null
}

interface ChunkItem {
  chunk_id: string
  doc_id: string
  chunk_index: number
  text: string
  metadata?: Record<string, unknown>
}

const documents = ref<DocItem[]>([])
const selectedDocId = ref('')
const loadingDocs = ref(true)
const loadingChunks = ref(false)
const error = ref('')

const chunks = ref<ChunkItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const route = useRoute()
const router = useRouter()

const selectedDoc = computed(() => documents.value.find((d) => d.doc_id === selectedDocId.value) || null)

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    queued: '排队中',
    processing: '解析中',
    done: '已完成',
    error: '失败',
  }
  return map[status] || status
}

async function refreshDocuments() {
  loadingDocs.value = true
  error.value = ''
  try {
    const resp = await apiClient.get('/documents')
    documents.value = resp.data.documents || []
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.response?.data?.message || e?.message || '加载文档列表失败'
  } finally {
    loadingDocs.value = false
  }
}

async function refreshChunks() {
  if (!selectedDocId.value) return
  loadingChunks.value = true
  error.value = ''
  try {
    const resp = await apiClient.get('/chunks', {
      params: { doc_id: selectedDocId.value, page: page.value, page_size: pageSize.value },
    })
    chunks.value = resp.data.chunks || []
    total.value = resp.data.total || 0
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.response?.data?.message || e?.message || '加载 Chunk 失败'
  } finally {
    loadingChunks.value = false
  }
}

function onDocChange() {
  page.value = 1
  router.replace({ query: { ...route.query, doc_id: selectedDocId.value || undefined } })
  refreshChunks()
}

function prevPage() {
  if (page.value <= 1) return
  page.value -= 1
  refreshChunks()
}

function nextPage() {
  if (page.value * pageSize.value >= total.value) return
  page.value += 1
  refreshChunks()
}

onMounted(async () => {
  await refreshDocuments()
  if (documents.value.length) {
    const fromQuery = String(route.query.doc_id || '')
    selectedDocId.value = documents.value.some((d) => d.doc_id === fromQuery) ? fromQuery : documents.value[0].doc_id
    await refreshChunks()
  }
})

watch(
  () => route.query.doc_id,
  async (val) => {
    const docId = String(val || '')
    if (!docId || docId === selectedDocId.value) return
    if (documents.value.some((d) => d.doc_id === docId)) {
      selectedDocId.value = docId
      page.value = 1
      await refreshChunks()
    }
  }
)
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

.hint-banner {
  background: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin: 14px 0;
}

.loading {
  color: #475569;
  font-size: 14px;
  padding: 20px 0;
  text-align: center;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.label {
  font-size: 12px;
  color: #475569;
  font-weight: 600;
}

.select {
  min-width: 320px;
  max-width: 100%;
  padding: 9px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #1e293b;
  font-size: 13px;
}
.select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.btn-secondary {
  background: #fff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
}
.btn-secondary:hover {
  background: #eff6ff;
}

.chunk-list {
  margin-top: 18px;
}

.chunk-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 12px;
}
.chunk-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.pager {
  display: flex;
  align-items: center;
  gap: 10px;
}
.page-info {
  font-size: 12px;
  color: #475569;
}

.chunk-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.chunk-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  color: #94a3b8;
  font-size: 12px;
}
.chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #0f172a;
  font-weight: 600;
}
.mono {
  font-family: 'SF Mono', 'Fira Code', Menlo, Consolas, monospace;
  font-size: 11.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chunk-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: #334155;
  font-size: 13px;
  line-height: 1.65;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #475569;
  background: #fff;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
}
.empty-state .icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.empty-state p {
  color: #475569;
  font-size: 14px;
}
</style>
