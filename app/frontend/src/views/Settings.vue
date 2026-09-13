<template>
  <div class="settings page-container">
    <header class="page-header">
      <h2 class="page-title">
        <span class="icon">⚙️</span>
        通知设置
      </h2>
      <p class="page-desc">配置企业微信机器人，接收 Emby 通知消息</p>
    </header>

    <div v-if="loading" class="loading">
      <span class="spinner"></span>
      加载中...
    </div>

    <form v-else @submit.prevent="saveConfig" class="settings-form">
      <!-- 企业微信配置 -->
      <div class="card">
        <h3 class="card-title">
          <span class="icon">💬</span>
          企业微信机器人
        </h3>
        
        <div class="form-group">
          <label>
            Webhook Key
            <span class="required">*</span>
          </label>
          <input 
            type="text" 
            v-model="config.webhook_key"
            class="form-input"
            placeholder="例如: 693a91f6-7xxx-4bc4-97a0-0ec2sfs60f"
            required
          />
          <span class="form-hint">
            在企业微信群中添加机器人后获取的 Key 值，
            <a href="https://work.weixin.qq.com/help?doc_id=13376" target="_blank">查看帮助</a>
          </span>
        </div>

        <div class="form-group">
          <label>
            机器人名称
            <span class="required">*</span>
          </label>
          <input 
            type="text" 
            v-model="config.bot_name"
            class="form-input"
            placeholder="Emby 通知助手"
            required
          />
        </div>

        <div class="form-group">
          <label>消息标题前缀</label>
          <input 
            type="text" 
            v-model="config.title_prefix"
            class="form-input"
            placeholder="例如: [Emby]"
          />
        </div>
      </div>

      <!-- 通知事件 -->
      <div class="card">
        <h3 class="card-title">
          <span class="icon">🔔</span>
          通知事件
        </h3>
        
        <div class="checkbox-list">
          <label class="checkbox-item">
            <input type="checkbox" v-model="config.events.library_new" />
            <span class="checkmark"></span>
            <span class="label">
              媒体库更新
              <span class="desc">当有新电影/电视剧入库时通知</span>
            </span>
          </label>

          <label class="checkbox-item">
            <input type="checkbox" v-model="config.events.playback_start" />
            <span class="checkmark"></span>
            <span class="label">
              播放开始
              <span class="desc">当用户开始播放时通知</span>
            </span>
          </label>

          <label class="checkbox-item">
            <input type="checkbox" v-model="config.events.playback_stop" />
            <span class="checkmark"></span>
            <span class="label">
              播放停止
              <span class="desc">当用户停止播放时通知</span>
            </span>
          </label>

          <label class="checkbox-item">
            <input type="checkbox" v-model="config.events.user_logged_in" />
            <span class="checkmark"></span>
            <span class="label">
              用户登录
              <span class="desc">当有新用户登录时通知</span>
            </span>
          </label>

          <label class="checkbox-item">
            <input type="checkbox" v-model="config.events.user_logged_out" />
            <span class="checkmark"></span>
            <span class="label">
              用户登出
              <span class="desc">当用户登出时通知</span>
            </span>
          </label>

          <label class="checkbox-item">
            <input type="checkbox" v-model="config.events.transcode_start" />
            <span class="checkmark"></span>
            <span class="label">
              转码开始
              <span class="desc">当开始转码时通知</span>
            </span>
          </label>
        </div>
      </div>

      <!-- TMDB 配置 -->
      <div class="card">
        <h3 class="card-title">
          <span class="icon">🎬</span>
          TMDB 配置
        </h3>
        <div class="form-group">
          <label>API Key</label>
          <input 
            type="text" 
            v-model="config.tmdb_api_key"
            class="form-input"
            placeholder="可选，用于获取电影海报"
          />
          <span class="form-hint">
            <a href="https://www.themoviedb.org/settings/api" target="_blank">获取 TMDB API Key</a>，用于获取更丰富的媒体信息
          </span>
        </div>
      </div>

      <!-- 其他设置 -->
      <div class="card">
        <h3 class="card-title">
          <span class="icon">📊</span>
          其他设置
        </h3>
        
        <div class="form-row">
          <div class="form-group">
            <label>事件保留天数</label>
            <input 
              type="number" 
              v-model.number="config.retention_days"
              class="form-input"
              min="1"
              max="365"
            />
          </div>

          <div class="form-group">
            <label>最大通知频率(秒)</label>
            <input 
              type="number" 
              v-model.number="config.rate_limit"
              class="form-input"
              min="0"
              placeholder="0 表示无限制"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="checkbox-item">
            <input type="checkbox" v-model="config.debug_mode" />
            <span class="checkmark"></span>
            <span class="label">
              调试模式
              <span class="desc">开启后会记录更多日志信息</span>
            </span>
          </label>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="saving">
          <span v-if="saving" class="spinner"></span>
          {{ saving ? '保存中...' : '保存设置' }}
        </button>
        <button type="button" class="btn btn-secondary" @click="testWebhook" :disabled="testing">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
      </div>

      <!-- 状态提示 -->
      <div v-if="message" class="form-message" :class="messageType">
        {{ message }}
      </div>
    </form>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'Settings',
  setup() {
    const loading = ref(false)
    const saving = ref(false)
    const testing = ref(false)
    const message = ref('')
    const messageType = ref('')

    const config = ref({
      webhook_key: '',
      bot_name: 'Emby 通知助手',
      title_prefix: '',
      events: {
        library_new: true,
        playback_start: false,
        playback_stop: false,
        user_logged_in: false,
        user_logged_out: false,
        transcode_start: false
      },
      tmdb_api_key: '',
      retention_days: 30,
      rate_limit: 5,
      debug_mode: false
    })

    // 获取配置
    const fetchConfig = async () => {
      loading.value = true
      try {
        const response = await fetch('/api/config')
        const data = await response.json()
        if (data.success && data.data) {
          // 合并配置
          config.value = { ...config.value, ...data.data }
        }
      } catch (error) {
        console.error('获取配置失败:', error)
        showMessage('获取配置失败，使用默认设置', 'warning')
      } finally {
        loading.value = false
      }
    }

    // 保存配置
    const saveConfig = async () => {
      saving.value = true
      try {
        const response = await fetch('/api/config', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(config.value)
        })
        const data = await response.json()
        if (data.success) {
          showMessage('保存成功！', 'success')
        } else {
          showMessage(data.message || '保存失败', 'error')
        }
      } catch (error) {
        console.error('保存配置失败:', error)
        showMessage('保存失败，请检查网络连接', 'error')
      } finally {
        saving.value = false
      }
    }

    // 测试 Webhook
    const testWebhook = async () => {
      if (!config.value.webhook_key) {
        showMessage('请先填写 Webhook Key', 'warning')
        return
      }
      
      testing.value = true
      try {
        const response = await fetch('/api/config/test', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ webhook_key: config.value.webhook_key })
        })
        const data = await response.json()
        if (data.success) {
          showMessage('测试消息发送成功！', 'success')
        } else {
          showMessage(data.message || '发送失败', 'error')
        }
      } catch (error) {
        console.error('测试失败:', error)
        showMessage('测试失败，请检查配置', 'error')
      } finally {
        testing.value = false
      }
    }

    // 显示消息
    const showMessage = (text, type = 'info') => {
      message.value = text
      messageType.value = type
      setTimeout(() => {
        message.value = ''
      }, 3000)
    }

    onMounted(() => {
      fetchConfig()
    })

    return {
      loading,
      saving,
      testing,
      config,
      message,
      messageType,
      saveConfig,
      testWebhook
    }
  }
}
</script>

<style scoped>
.settings-form {
  max-width: 1000px;
  width: 100%;
}

.checkbox-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
}

.form-message {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  text-align: center;
  font-size: 14px;
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
