<template>
  <div id="layout">
    <nav class="sidebar">
      <h1 class="brand">SimpleRAG</h1>
      <router-link to="/query">召回测试台</router-link>
      <router-link to="/profiles">Profiles</router-link>
      <router-link to="/documents">文档管理</router-link>
      <router-link to="/chunks">Chunk 预览</router-link>
      <router-link to="/experiments">实验回放</router-link>
    </nav>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
#layout { display: flex; min-height: 100vh; }
.sidebar {
  width: 200px; background: #1e1e2e; color: #cdd6f4; padding: 24px 16px;
  display: flex; flex-direction: column; gap: 8px;
}
.brand { font-size: 18px; font-weight: bold; margin-bottom: 24px; color: #89b4fa; }
.sidebar a {
  color: #a6adc8; text-decoration: none; padding: 8px 12px; border-radius: 6px; font-size: 14px;
}
.sidebar a:hover, .sidebar a.router-link-active { background: #313244; color: #cdd6f4; }
.content { flex: 1; padding: 0; background: #fff; }
</style>
