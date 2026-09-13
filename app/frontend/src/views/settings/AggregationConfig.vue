<template>
  <div class="card">
    <h3 class="card-title">
      <span class="icon">📦</span>
      聚合通知设置
    </h3>

    <div class="form-group">
      <label>单集事件聚合时间</label>
      <div class="input-with-unit">
        <input
          type="number"
          v-model.number="config.delay_seconds"
          class="form-input"
          min="0"
          max="60"
        />
        <span class="unit">秒</span>
      </div>
      <span class="form-hint">在此时间窗口内入库的同一剧集集数会被聚合为一条通知（0-60秒）</span>
    </div>

    <div class="form-actions">
      <button class="btn btn-primary" @click="saveConfig" :disabled="saving">
        <span v-if="saving" class="spinner"></span>
        {{ saving ? '保存中...' : '保存设置' }}
      </button>
    </div>

    <div v-if="message" class="form-message" :class="messageType">
      {{ message }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { getAggregationConfig, updateAggregationConfig } from '@/api'

export default {
  name: 'AggregationConfig',
  setup() {
    const saving = ref(false)
    const message = ref('')
    const messageType = ref('')

    const config = ref({
      delay_seconds: 15
    })

    const loadConfig = async () => {
      try {
        const res = await getAggregationConfig()
        if (res.success && res.data) {
          config.value.delay_seconds = res.data.delay_seconds ?? 15
        }
      } catch (error) {
        console.error('加载聚合配置失败:', error)
      }
    }

    const saveConfig = async () => {
      saving.value = true
      message.value = ''
      try {
        const res = await updateAggregationConfig({
          delay_seconds: config.value.delay_seconds
        })
        if (res.success) {
          showMessage('保存成功！', 'success')
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
      }, 3000)
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

.form-group label {
  display: block;
  font-weight: 500;
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.form-input {
  width: 120px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  transition: all var(--transition-fast);
  background: var(--bg-white);
}

.form-input:hover {
  border-color: var(--primary-color);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(74, 144, 217, 0.1);
}

.unit {
  color: var(--text-secondary);
  font-size: 14px;
}

.form-hint {
  display: block;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: var(--spacing-sm);
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
</style>
