<template>
  <div class="system-settings page-container">
    <header class="page-header">
      <h2 class="page-title">
        <span class="icon">⚙️</span>
        系统设置
      </h2>
      <p class="page-desc">配置系统参数和高级选项</p>
    </header>

    <div class="settings-list">
      <!-- 聚合通知设置 -->
      <AggregationConfig />

      <!-- 调试日志设置 -->
      <div class="card">
        <h3 class="card-title">
          <span class="icon">🐛</span>
          调试设置
        </h3>

        <div class="form-group">
          <label class="checkbox-item">
            <input
              type="checkbox"
              v-model="config.debug_logging"
            />
            <span class="checkmark"></span>
            <span class="label">
              <span class="label-text">启用调试日志</span>
              <span class="desc">开启后将显示详细的 DEBUG 级别日志，用于排查问题</span>
            </span>
          </label>
        </div>

        <div class="form-actions" style="margin-top: 16px;">
          <button class="btn btn-primary" @click="saveConfig" :disabled="saving">
            <span v-if="saving" class="spinner"></span>
            {{ saving ? '保存中...' : '保存设置' }}
          </button>
        </div>

        <!-- 状态提示 -->
        <div v-if="message" class="form-message" :class="messageType" style="margin-top: 12px;">
          {{ message }}
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import AggregationConfig from './settings/AggregationConfig.vue'
import { getSystemConfig, updateSystemConfig } from '@/api'

export default {
  name: 'SystemSettings',
  components: {
    AggregationConfig
  },
  setup() {
    const saving = ref(false)
    const message = ref('')
    const messageType = ref('')

    const config = ref({
      debug_logging: false
    })

    const loadConfig = async () => {
      try {
        const res = await getSystemConfig()
        if (res.success && res.data) {
          config.value.debug_logging = res.data.debug_logging || false
        }
      } catch (error) {
        console.error('加载系统配置失败:', error)
      }
    }

    const saveConfig = async () => {
      saving.value = true
      message.value = ''
      try {
        // 获取当前完整配置
        const currentRes = await getSystemConfig()
        const currentConfig = currentRes.success && currentRes.data ? currentRes.data : {}

        // 更新配置
        const res = await updateSystemConfig({
          ...currentConfig,
          debug_logging: config.value.debug_logging
        })

        if (res.success) {
          showMessage('保存成功！调试日志设置将在下次操作时生效', 'success')
        } else {
          showMessage(res.message || '保存失败', 'error')
        }
      } catch (error) {
        showMessage('保存失败: ' + error.message, 'error')
      } finally {
        saving.value = false
      }
    }

    const showMessage = (text, type) => {
      message.value = text
      messageType.value = type
      setTimeout(() => {
        message.value = ''
      }, 5000)
    }

    onMounted(() => {
      loadConfig()
    })

    return {
      config,
      saving,
      message,
      messageType,
      saveConfig
    }
  }
}
</script>

<style scoped>
.settings-list {
  max-width: 1000px;
  width: 100%;
}

.card {
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
  box-shadow: var(--shadow-sm);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--spacing-md) 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.card-title .icon {
  font-size: 20px;
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.checkbox-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.checkbox-item input {
  display: none;
}

.checkmark {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  margin-top: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.checkbox-item input:checked + .checkmark {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.checkbox-item input:checked + .checkmark::after {
  content: '✓';
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.label {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.label-text {
  font-weight: 500;
  color: var(--text-primary);
}

.desc {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: normal;
}

.form-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.form-message {
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  text-align: center;
  font-size: 14px;
  margin-top: var(--spacing-md);
}

.form-message.success {
  background: var(--success-light);
  color: var(--success-color);
}

.form-message.error {
  background: var(--error-light);
  color: var(--error-color);
}

.form-message.warning {
  background: var(--warning-light);
  color: var(--warning-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
  }

  .form-actions .btn {
    width: 100%;
  }
}
</style>
