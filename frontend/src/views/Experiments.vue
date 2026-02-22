<template>
  <div class="page">
    <h2>实验与回放</h2>
    <p class="desc">查看历史实验记录、A/B 对比、评测报表。</p>

    <div class="empty-state">
      <div class="icon">🔬</div>
      <p>暂无实验记录，运行检索测试后将自动记录。</p>
    </div>
    <!-- TODO: experiment list + detail + diff -->
  </div>
</template>

<script setup lang="ts">
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
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #475569;
  background: #f8fafc;
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
