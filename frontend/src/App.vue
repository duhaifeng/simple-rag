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
#layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  min-width: 220px;
  background: #1e293b;
  color: #e2e8f0;
  padding: 28px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border-right: 1px solid rgba(15, 23, 42, 0.5);
  box-shadow: 2px 0 16px rgba(2, 6, 23, 0.15);
}

.brand {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 28px;
  color: #60a5fa;
  letter-spacing: -0.3px;
}

.sidebar a {
  color: #cbd5e1;
  text-decoration: none;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
}

.sidebar a:hover {
  background: #334155;
  color: #e2e8f0;
}

.sidebar a.router-link-active {
  background: #3b82f6;
  color: #fff;
}

.content {
  flex: 1;
  padding: 0;
  background: #f8fafc;
  overflow-y: auto;
}
</style>
