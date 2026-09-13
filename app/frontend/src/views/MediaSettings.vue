<template>
  <div class="media-settings page-container">
    <header class="page-header">
      <h2 class="page-title">
        <span class="icon">🎬</span>
        媒体设置
      </h2>
      <p class="page-desc">配置 Emby 服务器、TMDB 和通知渠道</p>
    </header>

    <!-- Tab 导航 -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        class="tab-btn"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab 内容 -->
    <div class="tab-content">
      <WebhookConfig v-if="currentTab === 'webhook'" />
      <EmbyConfig v-if="currentTab === 'emby'" />
      <TmdbConfig v-if="currentTab === 'tmdb'" />
      <NotifyConfig v-if="currentTab === 'notify'" />
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import WebhookConfig from './settings/WebhookConfig.vue'
import EmbyConfig from './settings/EmbyConfig.vue'
import TmdbConfig from './settings/TmdbConfig.vue'
import NotifyConfig from './settings/NotifyConfig.vue'

export default {
  name: 'MediaSettings',
  components: {
    WebhookConfig,
    EmbyConfig,
    TmdbConfig,
    NotifyConfig
  },
  setup() {
    const currentTab = ref('webhook')

    const tabs = [
      { key: 'webhook', label: 'Webhook 配置', icon: '🔗' },
      { key: 'emby', label: 'Emby 配置', icon: '🎥' },
      { key: 'tmdb', label: 'TMDB 配置', icon: '🎬' },
      { key: 'notify', label: '通知配置', icon: '🔔' }
    ]

    return {
      currentTab,
      tabs
    }
  }
}
</script>

<style scoped>
.media-settings {
  max-width: 1000px;
  width: 100%;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  border-bottom: 2px solid var(--border-color);
  padding-bottom: var(--spacing-sm);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--primary-color);
  background: rgba(74, 144, 217, 0.05);
}

.tab-btn.active {
  color: var(--primary-color);
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--primary-color);
}

.tab-icon {
  font-size: 18px;
}

.tab-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 配置区块样式 */
:deep(.config-section) {
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

:deep(.section-title) {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-lg) 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

:deep(.section-title .icon) {
  font-size: 20px;
}

:deep(.form-actions) {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  .tab-btn {
    padding: 10px 16px;
    font-size: 13px;
    white-space: nowrap;
  }
  
  :deep(.form-actions) {
    flex-direction: column;
  }
  
  :deep(.form-actions .btn) {
    width: 100%;
  }
}
</style>
