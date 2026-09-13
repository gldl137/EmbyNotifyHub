<template>
  <div class="home">
    <div class="status-cards">
      <div class="card">
        <h3 class="card-title">服务状态</h3>
        <div class="status-item">
          <span>后端服务:</span>
          <span class="status-badge" :class="backendStatus ? 'status-online' : 'status-offline'">
            {{ backendStatus ? '运行中' : '离线' }}
          </span>
        </div>
        <div class="status-item">
          <span>前端服务:</span>
          <span class="status-badge status-online">运行中</span>
        </div>
      </div>

      <div class="card">
        <h3 class="card-title">Webhook 信息</h3>
        <div class="webhook-url">
          <code>{{ webhookUrl }}</code>
          <button class="btn btn-primary" @click="copyWebhook">复制</button>
        </div>
        <p class="hint">在 Emby Webhook 插件中配置此地址</p>
      </div>
    </div>

    <div class="card">
      <h3 class="card-title">快速操作</h3>
      <div class="actions">
        <button class="btn btn-primary" @click="testWebhook">测试 Webhook</button>
        <button class="btn btn-primary" @click="checkHealth">检查健康状态</button>
      </div>
      <div v-if="testResult" class="test-result">
        <pre>{{ JSON.stringify(testResult, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { getHealth } from '../api'

export default {
  name: 'Home',
  setup() {
    const backendStatus = ref(false)
    const testResult = ref(null)
    
    // 动态获取 Webhook URL（根据当前访问的地址）
    const webhookUrl = ref('')
    
    const updateWebhookUrl = () => {
      const baseUrl = window.location.origin
      webhookUrl.value = `${baseUrl}/webhook/emby`
    }

    const checkHealth = async () => {
      try {
        const data = await getHealth()
        backendStatus.value = data.status === 'healthy'
        testResult.value = data
      } catch (error) {
        backendStatus.value = false
        testResult.value = { error: '后端服务未启动' }
      }
    }

    const copyWebhook = () => {
      navigator.clipboard.writeText(webhookUrl.value)
      alert('已复制到剪贴板: ' + webhookUrl.value)
    }

    const testWebhook = async () => {
      try {
        const testData = {
          Event: 'library.new',
          Item: {
            Name: '测试电影',
            Type: 'Movie',
            Overview: '这是一条测试消息'
          }
        }
        const response = await fetch('/webhook/emby', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(testData)
        })
        testResult.value = await response.json()
      } catch (error) {
        testResult.value = { error: error.message }
      }
    }

    onMounted(() => {
      updateWebhookUrl()
      checkHealth()
    })

    return {
      backendStatus,
      testResult,
      webhookUrl,
      checkHealth,
      copyWebhook,
      testWebhook
    }
  }
}
</script>

<style scoped>
.home {
  max-width: 1000px;
  width: 100%;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border-light);
}

.status-item:last-child {
  border-bottom: none;
}

.webhook-url {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.webhook-url code {
  background: var(--bg-primary);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  font-family: 'Courier New', monospace;
  flex: 1;
}

.hint {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.test-result {
  background: var(--bg-primary);
  padding: 1rem;
  border-radius: var(--radius-sm);
  overflow-x: auto;
}

.test-result pre {
  margin: 0;
  font-size: 0.875rem;
}
</style>
