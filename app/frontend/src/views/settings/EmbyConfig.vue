<template>
  <div class="config-section">
    <!-- Emby 服务器列表 -->
    <div class="section-subtitle custom-notify-header">
      <span></span>
      <button class="btn btn-sm btn-primary" @click="openAddServerModal">
        <span class="icon">➕</span> 新增服务器
      </button>
    </div>

    <div class="server-list" v-if="servers.length > 0">
      <div 
        v-for="server in servers" 
        :key="server.id"
        class="server-item"
      >
        <div class="server-info">
          <span class="server-icon">🎥</span>
          <div class="server-detail">
            <span class="server-name">{{ server.name }}</span>
            <span class="server-url">{{ server.base_url }}</span>
            <span class="server-meta">
              <span class="server-status" :class="{ active: server.enabled }">
                {{ server.enabled ? '已启用' : '已禁用' }}
              </span>
              <span v-if="server.server_id" class="server-id" title="ServerId">ID: {{ server.server_id.substring(0, 8) }}...</span>
              <span v-else class="server-id warning" title="点击测试连接获取 ServerId">未识别</span>
            </span>
          </div>
        </div>
        <div class="server-actions">
          <button 
            class="btn btn-sm btn-primary" 
            @click="testServer(server)"
            :disabled="server.testing"
          >
            <span class="icon">🔌</span> 
            {{ server.testing ? '测试中...' : '测试' }}
          </button>
          <button class="btn btn-sm btn-secondary" @click="openEditServerModal(server)">
            <span class="icon">✏️</span> 编辑
          </button>
          <label class="switch">
            <input 
              type="checkbox" 
              v-model="server.enabled"
              @change="toggleServer(server)"
            />
            <span class="slider"></span>
          </label>
          <button class="btn btn-sm btn-danger" @click="deleteServer(server)">
            <span class="icon">🗑️</span>
          </button>
        </div>
      </div>
    </div>
    <div v-else class="empty-server-list">
      暂无 Emby 服务器，点击上方按钮添加
    </div>

    <!-- 服务器编辑弹窗 -->
    <div v-if="showServerModal" class="modal-overlay" @click="closeServerModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>{{ editingServer?.id ? '编辑' : '新增' }} Emby 服务器</h4>
          <button class="btn-close" @click="closeServerModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>服务器名称 <span class="auto-fetch-badge">自动获取</span></label>
            <input 
              type="text" 
              v-model="serverForm.name"
              class="form-input"
              placeholder="点击「连接」自动获取"
              readonly
              disabled
            />
            <span class="form-hint">服务器名称将通过「连接」按钮自动从 Emby 服务器获取</span>
          </div>
          <div class="form-group">
            <label>服务器地址（内网）</label>
            <input 
              type="text" 
              v-model="serverForm.base_url"
              class="form-input"
              placeholder="例如: http://192.168.1.100:8096"
            />
            <span class="form-hint">Emby 服务器的内网访问地址，用于 API 调用</span>
          </div>
          <div class="form-group">
            <label>外网访问地址</label>
            <input 
              type="text" 
              v-model="serverForm.external_url"
              class="form-input"
              placeholder="例如: https://emby.example.com"
            />
            <span class="form-hint">用于音乐封面图片访问，不填写则使用内网地址</span>
          </div>
          <div class="form-group">
            <label>API Key</label>
            <input 
              type="text" 
              v-model="serverForm.api_key"
              class="form-input"
              placeholder="Emby API Key"
            />
            <span class="form-hint">在 Emby 管理后台生成 API Key</span>
          </div>
          <div class="form-group" v-if="serverForm.server_id">
            <label>服务器标识 (ServerId)</label>
            <input 
              type="text" 
              v-model="serverForm.server_id"
              class="form-input"
              readonly
              disabled
            />
            <span class="form-hint">自动获取，用于多服务器识别</span>
          </div>
        </div>
        <div class="modal-footer">
          <span v-if="saveMessage" class="save-status" :class="{ success: saveSuccess, error: !saveSuccess }">
            {{ saveMessage }}
          </span>
          <button class="btn btn-secondary" @click="testServerForm" :disabled="formTesting || formConnected">
            {{ formTesting ? '连接中...' : (formConnected ? '已连接' : '连接') }}
          </button>
          <button class="btn btn-primary" @click="saveServer" :disabled="saving || !formConnected">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button class="btn btn-text" @click="closeServerModal">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'

export default {
  name: 'EmbyConfig',
  setup() {
    const servers = ref([])
    const showServerModal = ref(false)
    const editingServer = ref(null)
    const saving = ref(false)
    const formTesting = ref(false)
    const formConnected = ref(false)
    const saveSuccess = ref(false)
    const saveMessage = ref('')

    // 服务器表单
    const serverForm = reactive({
      id: null,
      name: '',
      base_url: '',
      external_url: '',
      api_key: '',
      enabled: true,
      server_id: ''
    })

    // 加载服务器列表
    const loadServers = async () => {
      try {
        const res = await fetch('/api/config/emby/servers')
        const data = await res.json()
        if (data.success) {
          servers.value = (data.data || []).map(s => ({...s, testing: false}))
        }
      } catch (e) {
        console.error('加载 Emby 服务器列表失败:', e)
      }
    }

    // 打开新增服务器弹窗
    const openAddServerModal = () => {
      editingServer.value = null
      formConnected.value = false
      Object.assign(serverForm, {
        id: null,
        name: '',
        base_url: '',
        external_url: '',
        api_key: '',
        enabled: true,
        server_id: ''
      })
      saveMessage.value = ''
      showServerModal.value = true
    }

    // 打开编辑服务器弹窗
    const openEditServerModal = (server) => {
      editingServer.value = server
      // 编辑已有服务器，如果已有 server_id 则认为已连接
      formConnected.value = !!server.server_id
      Object.assign(serverForm, {
        id: server.id,
        name: server.name || '',
        base_url: server.base_url || '',
        external_url: server.external_url || '',
        api_key: server.api_key || '',
        enabled: server.enabled,
        server_id: server.server_id || ''
      })
      saveMessage.value = formConnected.value ? '服务器已连接，可直接保存' : ''
      showServerModal.value = true
    }

    // 关闭弹窗
    const closeServerModal = () => {
      showServerModal.value = false
      editingServer.value = null
      saveMessage.value = ''
      formConnected.value = false
    }

    // 保存服务器
    const saveServer = async () => {
      // 验证连接状态（新增服务器时必须先连接成功）
      if (!formConnected.value) {
        saveSuccess.value = false
        saveMessage.value = '请先点击"连接"按钮连接服务器'
        return
      }

      // 验证必填项
      if (!serverForm.name || serverForm.name.trim() === '') {
        saveSuccess.value = false
        saveMessage.value = '服务器名称未获取，请重新连接'
        return
      }
      if (!serverForm.base_url || serverForm.base_url.trim() === '') {
        saveSuccess.value = false
        saveMessage.value = '请输入服务器地址'
        return
      }
      if (!serverForm.api_key || serverForm.api_key.trim() === '') {
        saveSuccess.value = false
        saveMessage.value = '请输入 API Key'
        return
      }

      saving.value = true
      saveSuccess.value = false
      saveMessage.value = ''

      try {
        const isEdit = !!editingServer.value
        const url = isEdit ? `/api/config/emby/servers/${editingServer.value.id}` : '/api/config/emby/servers'
        const method = isEdit ? 'PUT' : 'POST'

        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({...serverForm})
        })

        const data = await res.json()

        if (data.success) {
          await loadServers()
          saveSuccess.value = true
          saveMessage.value = '保存成功'
          setTimeout(() => {
            closeServerModal()
          }, 800)
        } else {
          saveSuccess.value = false
          saveMessage.value = data.message || '保存失败'
        }
      } catch (error) {
        console.error('保存 Emby 服务器出错:', error)
        saveSuccess.value = false
        saveMessage.value = '保存失败'
      } finally {
        saving.value = false
      }
    }

    // 测试服务器连接
    const testServer = async (server) => {
      server.testing = true
      try {
        const res = await fetch(`/api/config/emby/servers/${server.id}/test`, {
          method: 'POST'
        })
        const data = await res.json()
        alert(data.success ? '连接成功！' + (data.message || '') : '连接失败：' + (data.message || '未知错误'))
      } catch (error) {
        alert('测试失败')
      } finally {
        server.testing = false
      }
    }

    // 连接表单中的服务器
    const testServerForm = async () => {
      if (!serverForm.base_url || !serverForm.api_key) {
        saveSuccess.value = false
        saveMessage.value = '请先填写服务器地址和 API Key'
        return
      }

      formTesting.value = true
      formConnected.value = false
      try {
        const res = await fetch('/api/config/emby/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            base_url: serverForm.base_url,
            api_key: serverForm.api_key,
            server_config_id: editingServer.value?.id || null
          })
        })
        const data = await res.json()
        saveSuccess.value = data.success

        if (data.success) {
          // 自动填充服务器名称
          const serverName = data.data?.server_name
          const embyServerId = data.data?.server_id

          if (serverName) {
            serverForm.name = serverName
          }

          // 自动填充 ServerId
          if (embyServerId) {
            serverForm.server_id = embyServerId
          }

          // 标记已连接成功
          formConnected.value = true
          saveMessage.value = data.message || '连接成功，可以保存'
        } else {
          saveMessage.value = data.message || '连接失败，请检查地址和 API Key'
        }
      } catch (error) {
        saveSuccess.value = false
        formConnected.value = false
        saveMessage.value = '连接失败'
      } finally {
        formTesting.value = false
      }
    }

    // 删除服务器
    const deleteServer = async (server) => {
      if (!confirm(`确定要删除服务器 "${server.name}" 吗？`)) {
        return
      }

      try {
        const res = await fetch(`/api/config/emby/servers/${server.id}`, {
          method: 'DELETE'
        })
        const data = await res.json()
        if (data.success) {
          await loadServers()
        } else {
          alert(data.message || '删除失败')
        }
      } catch (error) {
        console.error('删除 Emby 服务器出错:', error)
        alert('删除失败')
      }
    }

    // 切换服务器启用状态
    const toggleServer = async (server) => {
      try {
        const res = await fetch(`/api/config/emby/servers/${server.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...server,
            enabled: server.enabled
          })
        })
        const data = await res.json()
        if (!data.success) {
          alert(data.message || '更新失败')
          server.enabled = !server.enabled
        }
      } catch (error) {
        console.error('切换服务器状态出错:', error)
        server.enabled = !server.enabled
      }
    }

    onMounted(() => {
      loadServers()
    })

    return {
      servers,
      showServerModal,
      editingServer,
      serverForm,
      saving,
      formTesting,
      formConnected,
      saveSuccess,
      saveMessage,
      openAddServerModal,
      openEditServerModal,
      closeServerModal,
      saveServer,
      testServer,
      testServerForm,
      deleteServer,
      toggleServer
    }
  }
}
</script>

<style scoped>
/* 服务器列表样式 */
.server-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.server-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
  gap: var(--spacing-md);
}

.server-item:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.server-info {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  flex: 1;
  min-width: 0;
}

.server-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.server-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.server-name {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 14px;
}

.server-url {
  font-size: 12px;
  color: var(--text-secondary);
}

.server-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: 2px;
}

.server-status {
  font-size: 11px;
  color: var(--text-tertiary);
}

.server-status.active {
  color: var(--success-color);
}

.server-id {
  font-size: 10px;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  font-family: monospace;
}

.server-id.warning {
  color: var(--warning-color);
  background: var(--warning-color-bg, rgba(255, 165, 0, 0.1));
}

.server-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.empty-server-list {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-color);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.modal-header h4 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.btn-close:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}

.save-status {
  margin-right: auto;
  font-size: 13px;
}

.save-status.success {
  color: var(--success-color);
}

.save-status.error {
  color: var(--danger-color);
}

/* 按钮样式 */
.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}

/* 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 20px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-tertiary);
  transition: .3s;
  border-radius: 20px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: .3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--primary-color);
}

input:checked + .slider:before {
  transform: translateX(20px);
}

/* 表单样式 */
.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  color: var(--text-secondary);
  font-size: 13px;
}

.auto-fetch-badge {
  display: inline-block;
  font-size: 10px;
  color: var(--success-color);
  background: rgba(34, 197, 94, 0.1);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  margin-left: var(--spacing-xs);
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  transition: all var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 复用通知配置的样式 */
.section-subtitle {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin: var(--spacing-lg) 0 var(--spacing-sm);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--border-color);
}

.custom-notify-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 响应式样式 */
@media (max-width: 768px) {
  .server-item {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .server-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .server-detail {
    min-width: 0;
  }

  .server-url {
    word-break: break-all;
  }
}
</style>
