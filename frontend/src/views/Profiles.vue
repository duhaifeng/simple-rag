<template>
  <div class="page">
    <h2>Profiles 管理</h2>
    <p class="desc">Embedding / VectorStore / Retrieval / Rerank profiles 的查看与切换。</p>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="loading" class="loading">加载中…</div>

    <template v-if="!loading && !error">
      <div v-for="(group, groupName) in profiles" :key="groupName" class="group">
        <div class="group-header">
          <h3>{{ groupLabels[groupName] || groupName }}</h3>
          <span class="active-badge">当前: {{ group.active }}</span>
        </div>

        <div class="profile-grid">
          <div
            v-for="p in group.profiles"
            :key="p.name"
            class="profile-card"
            :class="{ active: p.active }"
          >
            <div class="card-top">
              <span class="profile-name">{{ p.name }}</span>
              <span v-if="p.active" class="status-dot" title="Active" />
            </div>
            <div class="provider">{{ p.provider || '—' }}</div>
            <div v-if="p.config && Object.keys(p.config).length" class="config-table">
              <div v-for="(val, key) in p.config" :key="key" class="config-row">
                <span class="config-key">{{ key }}</span>
                <span class="config-val">{{ formatVal(val) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../api/client'

interface ProfileEntry {
  name: string
  provider: string
  active: boolean
  config: Record<string, unknown> | null
}

interface ProfileGroup {
  active: string
  profiles: ProfileEntry[]
}

const profiles = ref<Record<string, ProfileGroup>>({})
const loading = ref(true)
const error = ref('')

const groupLabels: Record<string, string> = {
  embeddings: 'Embeddings',
  vector_stores: 'Vector Stores',
  retrieval: 'Retrieval Strategy',
  rerank: 'Rerank',
}

function formatVal(val: unknown): string {
  if (val === null || val === undefined) return '—'
  if (typeof val === 'boolean') return val ? 'true' : 'false'
  return String(val)
}

onMounted(async () => {
  try {
    const resp = await apiClient.get('/profiles')
    profiles.value = resp.data
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.response?.data?.message || e?.message || '加载 Profiles 失败'
    console.error(e)
  } finally {
    loading.value = false
  }
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
.desc {
  color: #475569;
  margin-bottom: 28px;
}

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

.group {
  margin-bottom: 36px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}
.group-header h3 {
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}
.active-badge {
  font-size: 12px;
  color: #3b82f6;
  background: #eff6ff;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 500;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
}

.profile-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 18px 20px;
  transition: box-shadow 0.15s, border-color 0.15s;
}
.profile-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.profile-card.active {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.12);
}

.card-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.profile-name {
  font-weight: 600;
  font-size: 14px;
  color: #0f172a;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  flex-shrink: 0;
}

.provider {
  font-size: 12px;
  color: #475569;
  margin-bottom: 12px;
}

.config-table {
  border-top: 1px solid #f1f5f9;
  padding-top: 10px;
}
.config-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  font-size: 12px;
  line-height: 1.6;
}
.config-key {
  color: #475569;
}
.config-val {
  color: #1e293b;
  font-family: 'SF Mono', 'Fira Code', Menlo, Consolas, monospace;
  font-size: 11.5px;
  text-align: right;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
