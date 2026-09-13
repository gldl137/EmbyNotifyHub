<template>
  <div class="card">
    <h3 class="card-title">
      <span class="icon">🎬</span>
      TMDB 配置
    </h3>
    
    <div class="form-group">
      <label>TMDB API Key</label>
      <input 
        type="text" 
        v-model="config.api_key"
        class="form-input"
        placeholder="输入 TMDB API Key"
      />
      <span class="form-hint">
        <a href="https://www.themoviedb.org/settings/api" target="_blank">获取 TMDB API Key</a>
        ，用于获取电影海报和详细信息
      </span>
    </div>

    <!-- 代理设置 -->
    <div class="form-group">
      <label class="checkbox-item">
        <input 
          type="checkbox" 
          v-model="config.proxy_enabled"
          @change="saveConfig"
        />
        <span class="checkmark"></span>
        <span class="label">
          <span class="label-text">使用代理访问 TMDB</span>
          <span class="desc">当无法直接访问 TMDB 时，可通过代理服务器访问</span>
        </span>
      </label>
    </div>

    <div class="form-group" v-if="config.proxy_enabled">
      <label>代理服务器地址</label>
      <input 
        type="text" 
        v-model="config.proxy_url"
        class="form-input"
        placeholder="例如: http://127.0.0.1:7890 或 socks5://127.0.0.1:1080"
        @change="saveConfig"
      />
      <span class="form-hint">
        支持 HTTP/HTTPS/SOCKS5 代理格式
      </span>
    </div>

    <div class="form-actions">
      <button class="btn btn-secondary" @click="testConfig" :disabled="testing">
        {{ testing ? '测试中...' : '测试连接' }}
      </button>
      <button class="btn btn-primary" @click="saveConfig" :disabled="saving">
        {{ saving ? '保存中...' : '保存配置' }}
      </button>
    </div>
    
    <div v-if="saveStatus" class="form-message" :class="saveStatus.type">
      {{ saveStatus.message }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { getTmdbConfig, updateTmdbConfig, testTmdbConfig } from '@/api'

export default {
  name: 'TmdbConfig',
  setup() {
    const config = ref({
      api_key: '',
      proxy_enabled: false,
      proxy_url: ''
    })
    const saving = ref(false)
    const testing = ref(false)
    const saveStatus = ref(null)

    // 加载配置
    const loadConfig = async () => {
      try {
        const res = await getTmdbConfig()
        if (res.success && res.data) {
          config.value = {
            api_key: res.data.api_key || '',
            proxy_enabled: res.data.proxy_enabled || false,
            proxy_url: res.data.proxy_url || ''
          }
        }
      } catch (e) {
        console.error('加载TMDB配置失败:', e)
      }
    }

    const saveConfig = async () => {
      saving.value = true
      saveStatus.value = null
      try {
        const res = await updateTmdbConfig({
          api_key: config.value.api_key,
          proxy_enabled: config.value.proxy_enabled,
          proxy_url: config.value.proxy_url
        })
        if (res.success) {
          saveStatus.value = { type: 'success', message: '保存成功！' }
        } else {
          saveStatus.value = { type: 'error', message: '保存失败：' + (res.message || '未知错误') }
        }
      } catch (e) {
        saveStatus.value = { type: 'error', message: '保存失败：' + e.message }
      } finally {
        saving.value = false
        setTimeout(() => {
          saveStatus.value = null
        }, 3000)
      }
    }

    const testConfig = async () => {
      if (!config.value.api_key) {
        saveStatus.value = { type: 'error', message: '请先输入 API Key' }
        return
      }
      testing.value = true
      saveStatus.value = null
      try {
        const res = await testTmdbConfig()
        if (res.success) {
          saveStatus.value = { type: 'success', message: '测试成功：' + res.message }
        } else {
          saveStatus.value = { type: 'error', message: '测试失败：' + (res.message || '未知错误') }
        }
      } catch (e) {
        saveStatus.value = { type: 'error', message: '测试失败：' + e.message }
      } finally {
        testing.value = false
        setTimeout(() => {
          saveStatus.value = null
        }, 5000)
      }
    }

    onMounted(() => {
      loadConfig()
    })

    return {
      config,
      saving,
      testing,
      saveStatus,
      saveConfig,
      testConfig
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

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  transition: all var(--transition-fast);
  box-sizing: border-box;
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

.form-hint {
  display: block;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: var(--spacing-sm);
}

.form-hint a {
  color: var(--primary-color);
  text-decoration: none;
}

.form-hint a:hover {
  text-decoration: underline;
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
</style>
