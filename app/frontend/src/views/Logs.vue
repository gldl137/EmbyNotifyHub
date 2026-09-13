<template>
  <div class="logs">
    <div class="card">
      <div class="logs-header">
        <h3 class="card-title">通知日志</h3>
        <button class="btn btn-primary" @click="refreshLogs">刷新</button>
      </div>
      <div class="logs-list">
        <div v-if="logs.length === 0" class="empty-state">
          暂无日志记录
        </div>
        <div v-else v-for="(log, index) in logs" :key="index" class="log-item">
          <div class="log-time">{{ log.time }}</div>
          <div class="log-content">
            <span class="log-event">{{ log.event }}</span>
            <span class="log-name">{{ log.name }}</span>
            <span :class="['log-status', log.status]">{{ log.statusText }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'Logs',
  setup() {
    const logs = ref([])

    const refreshLogs = () => {
      // 模拟日志数据，实际应从后端API获取
      logs.value = [
        {
          time: new Date().toLocaleString(),
          event: '🎬 新片入库',
          name: '蜜语纪',
          status: 'success',
          statusText: '发送成功'
        }
      ]
    }

    onMounted(() => {
      refreshLogs()
    })

    return {
      logs,
      refreshLogs
    }
  }
}
</script>

<style scoped>
.logs {
  max-width: 1000px;
  width: 100%;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.logs-list {
  max-height: 600px;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-tertiary);
}

.log-item {
  display: flex;
  padding: 1rem;
  border-bottom: 1px solid var(--border-light);
  align-items: center;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: var(--text-tertiary);
  font-size: 0.875rem;
  width: 180px;
  flex-shrink: 0;
}

.log-content {
  flex: 1;
  display: flex;
  gap: 1rem;
  align-items: center;
}

.log-event {
  font-weight: 500;
  color: var(--text-primary);
}

.log-name {
  flex: 1;
  color: var(--text-secondary);
}

.log-status {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
}

.log-status.success {
  background-color: var(--success-light);
  color: var(--success-color);
}

.log-status.error {
  background-color: var(--error-light);
  color: var(--error-color);
}
</style>
