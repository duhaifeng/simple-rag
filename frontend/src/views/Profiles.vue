<template>
  <div class="page">
    <h2>Profiles 管理</h2>
    <p>Embedding / VectorStore / Retrieval / Rerank profiles 的查看与切换。</p>
    <!-- TODO: profile list, editor, version history -->
    <pre>{{ JSON.stringify(profiles, null, 2) }}</pre>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '../api/client'

const profiles = ref<Record<string, unknown>>({})

onMounted(async () => {
  try {
    const resp = await apiClient.get('/profiles')
    profiles.value = resp.data
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.page { max-width: 900px; margin: 0 auto; padding: 24px; }
pre { background: #f5f5f5; padding: 16px; border-radius: 8px; overflow: auto; }
</style>
