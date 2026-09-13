<template>
  <div class="config-section">
    <!-- Webhook 配置 -->
    <div class="webhook-section">
      <h4 class="subsection-title">
        <span class="icon">🔗</span>
        Webhook 配置
      </h4>
      <p class="description">在 Emby 服务器设置中添加以下 Webhook URL：</p>
      <div class="webhook-input-group">
        <input type="text" class="form-input webhook-url" :value="webhookUrl" readonly />
        <button class="btn btn-primary" @click="copyWebhook">
          {{ copied ? '已复制!' : '复制' }}
        </button>
      </div>
      <span class="form-hint">配置后，Emby 的事件将自动发送到该地址</span>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'WebhookConfig',
  setup() {
    const copied = ref(false)
    const webhookUrl = `${window.location.origin}/webhook/emby`

    const copyWebhook = () => {
      navigator.clipboard.writeText(webhookUrl)
      copied.value = true
      setTimeout(() => copied.value = false, 2000)
    }

    return {
      copied,
      webhookUrl,
      copyWebhook
    }
  }
}
</script>

<style scoped>
.webhook-section {
  margin-bottom: var(--spacing-lg);
}

.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.subsection-title .icon {
  font-size: 16px;
}

.description {
  color: var(--text-secondary);
  font-size: 13px;
  margin: 0 0 var(--spacing-sm) 0;
}

.webhook-input-group {
  display: flex;
  gap: var(--spacing-sm);
}

.webhook-url {
  flex: 1;
  font-family: monospace;
  font-size: 12px;
}
</style>
