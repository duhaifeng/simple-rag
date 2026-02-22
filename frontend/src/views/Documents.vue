<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>文档管理</h2>
        <p class="desc">上传文档、查看解析状态，管理已有文档。</p>
      </div>
      <div class="header-actions">
        <button class="btn-secondary" @click="reindexVectors" :disabled="reindexing">
          {{ reindexing ? '重建中…' : '重建向量索引' }}
        </button>
        <button class="btn-upload" @click="triggerFileInput">
          <span class="btn-icon">+</span> 上传文档
        </button>
      </div>
      <input
        ref="fileInputRef"
        type="file"
        multiple
        accept=".txt,.md,.markdown,.log,.csv,.json,.html,.htm"
        style="display: none"
        @change="onFileSelected"
      />
    </div>

    <div
      class="dropzone"
      :class="{ dragging }"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
      @click="triggerFileInput"
    >
      <div class="dropzone-inner">
        <div class="dropzone-icon">&#8682;</div>
        <p class="dropzone-title">拖拽文件到此处，或点击选择文件</p>
        <p class="dropzone-hint">支持 TXT、Markdown、CSV、JSON、HTML</p>
      </div>
    </div>

    <div v-if="uploadQueue.length" class="upload-queue">
      <div v-for="item in uploadQueue" :key="item.id" class="upload-item">
        <div class="upload-name">{{ item.file.name }}</div>
        <div class="upload-size">{{ formatSize(item.file.size) }}</div>
        <div class="upload-status" :class="item.status">
          <template v-if="item.status === 'uploading'">上传中…</template>
          <template v-else-if="item.status === 'success'">已上传</template>
          <template v-else-if="item.status === 'error'">失败</template>
          <template v-else>等待中</template>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="loading" class="loading">加载中…</div>

    <template v-if="!loading && documents.length">
      <h3 class="section-title">文档列表（{{ total }} 篇）</h3>
      <div class="doc-table-wrap">
        <table class="doc-table">
          <thead>
            <tr>
              <th>文件名</th>
              <th>状态</th>
              <th>文档 ID</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in documents" :key="doc.doc_id">
              <td class="cell-name">{{ doc.filename }}</td>
              <td>
                <span class="status-tag" :class="doc.status">{{ statusLabel(doc.status) }}</span>
                <div v-if="doc.status === 'error' && doc.error" class="status-error">{{ doc.error }}</div>
              </td>
              <td class="cell-id">{{ doc.doc_id }}</td>
              <td>
                <button class="btn-sm btn-danger" @click="deleteDoc(doc.doc_id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-if="!loading && !error && !documents.length && !uploadQueue.length" class="empty-state">
      <div class="icon">&#128196;</div>
      <p>暂无文档，请点击上方按钮或拖拽文件到上方区域开始上传。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import apiClient from '../api/client'

interface DocItem {
  doc_id: string
  filename: string
  status: string
  error?: string | null
}

interface UploadQueueItem {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
}

const fileInputRef = ref<HTMLInputElement | null>(null)
const documents = ref<DocItem[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref('')
const dragging = ref(false)
const uploadQueue = ref<UploadQueueItem[]>([])
let pollTimer: number | null = null
const reindexing = ref(false)

async function refreshDocuments(opts: { silent?: boolean } = {}) {
  const silent = opts.silent ?? false
  if (!silent) {
    loading.value = true
    error.value = ''
  }
  try {
    const resp = await apiClient.get('/documents')
    documents.value = resp.data.documents || []
    total.value = resp.data.total || 0
  } catch (e: any) {
    if (!silent) {
      error.value = e?.response?.data?.detail || e?.response?.data?.message || e?.message || '加载文档列表失败'
    }
  } finally {
    if (!silent) loading.value = false
  }
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    enqueueFiles(Array.from(input.files))
    input.value = ''
  }
}

function onDrop(e: DragEvent) {
  dragging.value = false
  if (e.dataTransfer?.files) {
    enqueueFiles(Array.from(e.dataTransfer.files))
  }
}

function enqueueFiles(files: File[]) {
  const items: UploadQueueItem[] = files.map((f) => ({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    file: f,
    status: 'pending',
  }))
  uploadQueue.value.push(...items)
  processQueue()
}

async function processQueue() {
  const pending = uploadQueue.value.filter((i) => i.status === 'pending')
  for (const item of pending) {
    item.status = 'uploading'
    try {
      const form = new FormData()
      form.append('file', item.file)
      const resp = await apiClient.post('/documents/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      item.status = 'success'
      documents.value.unshift({
        doc_id: resp.data.doc_id,
        filename: resp.data.filename,
        status: resp.data.status,
      })
      total.value += 1
      refreshDocuments({ silent: true })
    } catch {
      item.status = 'error'
    }
  }
  setTimeout(() => {
    uploadQueue.value = uploadQueue.value.filter((i) => i.status !== 'success')
  }, 2000)
}

async function deleteDoc(docId: string) {
  if (!confirm('确认删除该文档及其所有 Chunk？')) return
  try {
    await apiClient.delete(`/documents/${docId}`)
    refreshDocuments({ silent: true })
  } catch (e: any) {
    alert(e?.response?.data?.detail || e?.response?.data?.message || '删除失败')
  }
}

async function reindexVectors() {
  reindexing.value = true
  try {
    await apiClient.post('/documents/reindex_vectors')
    alert('已触发向量索引重建任务。根据文档数量可能需要一段时间。')
  } catch (e: any) {
    alert(e?.response?.data?.detail || e?.response?.data?.message || e?.message || '触发重建失败')
  } finally {
    reindexing.value = false
  }
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    queued: '排队中',
    processing: '解析中',
    done: '已完成',
    error: '失败',
  }
  return map[status] || status
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(async () => {
  await refreshDocuments()
  pollTimer = window.setInterval(() => {
    const hasActive = documents.value.some((d) => d.status === 'queued' || d.status === 'processing')
    if (hasActive) refreshDocuments({ silent: true })
  }, 1500)
})

onBeforeUnmount(() => {
  if (pollTimer) window.clearInterval(pollTimer)
  pollTimer = null
})
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

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.page-header h2 {
  margin-bottom: 4px;
}
.desc {
  color: #475569;
  margin-bottom: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}

.btn-upload {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  font-size: 14px;
  white-space: nowrap;
  flex-shrink: 0;
}
.btn-secondary {
  background: #fff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  padding: 10px 16px;
  font-size: 14px;
}
.btn-secondary:hover {
  background: #eff6ff;
}

.btn-icon {
  font-size: 18px;
  font-weight: 600;
  line-height: 1;
}

/* ---- Dropzone ---- */
.dropzone {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 36px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  margin-bottom: 24px;
  background: #fff;
}
.dropzone:hover,
.dropzone.dragging {
  border-color: #3b82f6;
  background: #eff6ff;
}
.dropzone-icon {
  font-size: 36px;
  color: #94a3b8;
  margin-bottom: 8px;
  transition: color 0.2s;
}
.dropzone:hover .dropzone-icon,
.dropzone.dragging .dropzone-icon {
  color: #3b82f6;
}
.dropzone-title {
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  margin: 0 0 4px;
}
.dropzone-hint {
  font-size: 12px;
  color: #475569;
  margin: 0;
}

/* ---- Upload queue ---- */
.upload-queue {
  margin-bottom: 24px;
}
.upload-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 6px;
  font-size: 13px;
}
.upload-name {
  flex: 1;
  font-weight: 500;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.upload-size {
  color: #94a3b8;
  font-size: 12px;
  flex-shrink: 0;
}
.upload-status {
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}
.upload-status.uploading { color: #f59e0b; }
.upload-status.success { color: #22c55e; }
.upload-status.error { color: #ef4444; }
.upload-status.pending { color: #94a3b8; }

/* ---- Error / Loading ---- */
.error-banner {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 14px;
  margin-bottom: 20px;
}
.loading {
  color: #475569;
  font-size: 14px;
  padding: 40px 0;
  text-align: center;
}

/* ---- Document table ---- */
.section-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 14px;
}

.doc-table-wrap {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}
.doc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.doc-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.doc-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}
.doc-table tr:last-child td {
  border-bottom: none;
}
.doc-table tr:hover td {
  background: #f8fafc;
}

.cell-name {
  font-weight: 500;
  color: #0f172a;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cell-id {
  font-family: 'SF Mono', 'Fira Code', Menlo, Consolas, monospace;
  font-size: 11.5px;
  color: #64748b;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-error {
  margin-top: 6px;
  color: #9f1239;
  font-size: 12px;
  max-width: 420px;
  white-space: pre-wrap;
}

/* ---- Status tag ---- */
.status-tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 20px;
}
.status-tag.queued {
  color: #d97706;
  background: #fffbeb;
}
.status-tag.processing {
  color: #2563eb;
  background: #eff6ff;
}
.status-tag.done {
  color: #16a34a;
  background: #f0fdf4;
}
.status-tag.error {
  color: #dc2626;
  background: #fef2f2;
}

/* ---- Buttons ---- */
.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
  border-radius: 6px;
}
.btn-danger {
  background: #fff;
  color: #ef4444;
  border: 1px solid #fecaca;
}
.btn-danger:hover {
  background: #fef2f2;
}

/* ---- Empty ---- */
.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: #475569;
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
