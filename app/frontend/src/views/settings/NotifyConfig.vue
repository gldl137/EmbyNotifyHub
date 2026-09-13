<template>
  <div class="config-section">
    <!-- 通知列表 -->
    <div class="section-subtitle custom-notify-header">
      <button class="btn btn-sm btn-primary" @click="openAddCustomModal">
        <span class="icon">➕</span> 新增通知
      </button>
      <span></span>
    </div>
    <div class="notify-channels" v-if="customNotifies.length > 0">
      <div 
        v-for="notify in customNotifies" 
        :key="notify.id"
        class="channel-item"
      >
        <div class="channel-info">
          <span class="channel-icon">{{ notify.channel_type === 'wecom_webhook' ? '💬' : '🏢' }}</span>
          <div class="channel-detail">
            <span class="channel-name">{{ notify.name }}</span>
            <span class="channel-type">{{ notify.channel_type === 'wecom_webhook' ? '群机器人' : '企业微信应用' }}</span>
            <span class="channel-status" :class="{ active: notify.enabled }">
              {{ notify.enabled ? '已启用' : '已禁用' }}
            </span>
          </div>
        </div>
        <div class="channel-actions">
          <button 
            class="btn btn-sm btn-primary" 
            @click="testCustomNotify(notify)"
            :disabled="notify.testing"
          >
            <span class="icon">🔔</span> 
            {{ notify.testing ? '测试中...' : '测试' }}
          </button>
          <button class="btn btn-sm btn-secondary" @click="openEditCustomModal(notify)">
            <span class="icon">✏️</span> 编辑
          </button>
          <button class="btn btn-sm btn-info" @click="openCustomEventsModal(notify)">
            <span class="icon">📋</span> 事件
          </button>
          <button class="btn btn-sm btn-info" @click="openCustomServersModal(notify)">
            <span class="icon">🖥️</span> 服务器
          </button>
          <label class="switch">
            <input 
              type="checkbox" 
              v-model="notify.enabled"
              @change="toggleCustomNotify(notify)"
            />
            <span class="slider"></span>
          </label>
          <button class="btn btn-sm btn-danger" @click="deleteCustomNotify(notify)">
            <span class="icon">🗑️</span>
          </button>
        </div>
      </div>
    </div>
    <div v-else class="empty-custom-notify">
      暂无通知渠道，点击上方按钮添加
    </div>

    <!-- 自定义通知编辑弹窗 -->
    <div v-if="showCustomModal" class="modal-overlay" @click="closeCustomModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>{{ editingCustomNotify?.id ? '编辑' : '新增' }}自定义通知</h4>
          <button class="btn-close" @click="closeCustomModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>渠道类型</label>
            <select v-model="customForm.channel_type" class="form-input">
              <option value="wecom_webhook">企业微信群机器人</option>
              <option value="wecom_app">企业微信应用</option>
            </select>
          </div>
          <div class="form-group">
            <label>通知名称</label>
            <input 
              type="text" 
              v-model="customForm.name"
              class="form-input"
              placeholder="输入通知名称"
            />
          </div>

          <!-- 群机器人配置 -->
          <template v-if="customForm.channel_type === 'wecom_webhook'">
            <div class="form-group">
              <label>Webhook Key</label>
              <input
                type="text"
                v-model="customForm.webhook_key"
                class="form-input"
                placeholder="输入 Webhook Key"
              />
              <span class="form-hint">企业微信群机器人 Webhook 地址中的 key 参数</span>
            </div>
          </template>

          <!-- 企业微信应用配置 -->
          <template v-if="customForm.channel_type === 'wecom_app'">
            <div class="form-group">
              <label>CorpID</label>
              <input 
                type="text" 
                v-model="customForm.corp_id"
                class="form-input"
                placeholder="企业微信 CorpID"
              />
            </div>
            <div class="form-group">
              <label>AgentID</label>
              <input 
                type="text" 
                v-model="customForm.agent_id"
                class="form-input"
                placeholder="应用 AgentID"
              />
            </div>
            <div class="form-group">
              <label>Secret</label>
              <input 
                type="text" 
                v-model="customForm.secret"
                class="form-input"
                placeholder="应用 Secret"
              />
            </div>
            <div class="form-group">
              <label>接收用户</label>
              <input 
                type="text" 
                v-model="customForm.to_user"
                class="form-input"
                placeholder="@all"
              />
            </div>
          </template>
        </div>
        <div class="modal-footer">
          <span v-if="customSaveMessage" class="save-status" :class="{ success: customSaveSuccess, error: !customSaveSuccess }">
            {{ customSaveMessage }}
          </span>
          <button class="btn btn-secondary" @click="testCustomForm" :disabled="customTesting">
            {{ customTesting ? '测试中...' : '发送测试' }}
          </button>
          <button class="btn btn-primary" @click="saveCustomNotify" :disabled="customSaving">
            {{ customSaving ? '保存中...' : '保存' }}
          </button>
          <button class="btn btn-text" @click="closeCustomModal">取消</button>
        </div>
      </div>
    </div>

    <!-- 事件选择弹窗 -->
    <div v-if="showEventsModal" class="modal-overlay" @click="closeEventsModal">
      <div class="modal-content events-modal" @click.stop>
        <div class="modal-header">
          <h4>{{ eventsChannel?.name || eventsCustomNotify?.name }} - 选择要发送的事件类型</h4>
          <button class="btn-close" @click="closeEventsModal">×</button>
        </div>
        <div class="modal-body">
          <div class="events-loading" v-if="loadingEvents">
            加载中...
          </div>
          <div class="events-list" v-else>
            <div 
              v-for="category in availableEvents" 
              :key="category.category"
              class="event-category"
            >
              <div class="category-header">
                <span class="category-name">{{ category.category_name }}</span>
              </div>
              <div class="category-events">
                <label 
                  v-for="event in category.events" 
                  :key="event.event_type"
                  class="event-checkbox"
                  :class="{ checked: selectedEvents.includes(event.event_type) }"
                >
                  <input 
                    type="checkbox" 
                    :value="event.event_type"
                    v-model="selectedEvents"
                  />
                  <span class="event-emoji">{{ event.emoji }}</span>
                  <span class="event-name">{{ event.description }}</span>
                  <span class="event-type">{{ event.event_type }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <span v-if="saveMessage" class="save-status" :class="{ success: saveSuccess, error: !saveSuccess }">
            {{ saveMessage }}
          </span>
          <div class="events-actions">
            <button class="btn btn-sm btn-text" @click="selectAllEvents">
              全选
            </button>
            <button class="btn btn-sm btn-text" @click="deselectAllEvents">
              全不选
            </button>
            <button class="btn btn-sm btn-text" @click="resetDefaultEvents">
              恢复默认
            </button>
          </div>
          <button class="btn btn-secondary" @click="saveEventsConfig" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button class="btn btn-text" @click="closeEventsModal">取消</button>
        </div>
      </div>
    </div>

    <!-- 服务器选择弹窗 -->
    <div class="modal-overlay" v-if="showServersModal" @click.self="showServersModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h4>{{ serversTargetName }} - 服务器过滤</h4>
          <button class="btn-close" @click="showServersModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="server-filter">
            <label 
              v-for="srv in embyServers" 
              :key="srv.id"
              class="server-checkbox"
            >
              <input 
                type="checkbox" 
                :value="srv.id"
                v-model="selectedServers"
              />
              <span class="server-name">{{ srv.name || srv.id }}</span>
              <span class="server-url" v-if="srv.server_url">{{ srv.server_url }}</span>
            </label>
          </div>
          <p class="form-hint" v-if="embyServers.length === 0">暂未配置 Emby 服务器</p>
          <p class="form-hint" v-else>不勾选任何服务器 = 接收所有 Emby 服务器的通知；勾选后仅勾选的服务器会发送此通知。</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showServersModal = false">取消</button>
          <button class="btn btn-primary" @click="saveCustomServers">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'

export default {
  name: 'NotifyConfig',
  setup() {
    const showEventsModal = ref(false)
    const eventsCustomNotify = ref(null)
    const eventsChannel = ref(null)
    const saving = ref(false)
    const loadingEvents = ref(false)
    const availableEvents = ref([])
    const selectedEvents = ref([])
    const defaultEvents = ['library.new', 'library.new.music', 'playback.start', 'playback.stop', 'system.webhooktest', 'system.notificationtest']
    
    // 保存状态提示
    const saveSuccess = ref(false)
    const saveMessage = ref('')

    // 自定义通知相关
    const showCustomModal = ref(false)
    const customNotifies = ref([])
    const editingCustomNotify = ref(null)
    const customSaving = ref(false)
    const customTesting = ref(false)
    const customSaveSuccess = ref(false)
    const customSaveMessage = ref('')

    // 自定义通知表单
    const customForm = reactive({
      id: null,
      name: '',
      enabled: true,
      channel_type: 'wecom_webhook',
      webhook_key: '',
      corp_id: '',
      agent_id: '',
      secret: '',
      to_user: '@all',
      allowed_events: [...defaultEvents],
      allowed_servers: []
    })

    // Emby 服务器列表（用于服务器过滤）
    const embyServers = ref([])
    const loadEmbyServers = async () => {
      try {
        const res = await fetch('/api/config/emby/servers')
        const data = await res.json()
        if (data.success) {
          embyServers.value = data.data || []
        }
      } catch (e) {
        console.error('加载 Emby 服务器失败:', e)
      }
    }



    // 加载所有可用的事件类型
    const loadAvailableEvents = async () => {
      try {
        loadingEvents.value = true
        const res = await fetch('/api/config/notify/events')
        const data = await res.json()
        if (data.success) {
          availableEvents.value = data.data || []
        }
      } catch (e) {
        console.error('加载事件类型失败:', e)
      } finally {
        loadingEvents.value = false
      }
    }

    // 加载自定义通知列表
    const loadCustomNotifies = async () => {
      try {
        const res = await fetch('/api/config/notify/custom')
        const data = await res.json()
        if (data.success) {
          customNotifies.value = (data.data || []).map(n => ({...n, testing: false}))
        }
      } catch (e) {
        console.error('加载自定义通知失败:', e)
      }
    }

    // 保存自定义通知事件配置
    const saveCustomNotifyEvents = async (notifyId) => {
      try {
        const res = await fetch(`/api/config/notify/custom/${notifyId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...eventsCustomNotify.value,
            allowed_events: selectedEvents.value
          })
        })
        const data = await res.json()
        return data.success
      } catch (e) {
        console.error('保存自定义通知事件配置失败:', e)
        return false
      }
    }

    // 全选事件
    const selectAllEvents = () => {
      const all = []
      for (const category of availableEvents.value) {
        for (const event of (category.events || [])) {
          all.push(event.event_type)
        }
      }
      selectedEvents.value = all
    }

    // 全不选事件
    const deselectAllEvents = () => {
      selectedEvents.value = []
    }

    // 恢复默认事件
    const resetDefaultEvents = () => {
      selectedEvents.value = [...defaultEvents]
    }

    // 关闭事件选择弹窗
    const closeEventsModal = () => {
      showEventsModal.value = false
      eventsCustomNotify.value = null
      eventsChannel.value = null
    }

    // 保存事件配置
    const saveEventsConfig = async () => {
      saving.value = true
      saveSuccess.value = false
      saveMessage.value = ''
      
      try {
        let success = false
        
        if (eventsCustomNotify.value) {
          // 保存自定义通知事件
          success = await saveCustomNotifyEvents(eventsCustomNotify.value.id)
          if (success) {
            eventsCustomNotify.value.allowed_events = [...selectedEvents.value]
          }
        }
        
        if (success) {
          await loadCustomNotifies()
          saveSuccess.value = true
          saveMessage.value = '保存成功'
          setTimeout(() => {
            closeEventsModal()
            saveSuccess.value = false
            saveMessage.value = ''
          }, 800)
        } else {
          saveSuccess.value = false
          saveMessage.value = '保存失败'
        }
      } catch (error) {
        console.error('保存事件配置出错:', error)
        saveSuccess.value = false
        saveMessage.value = '保存失败'
      } finally {
        saving.value = false
      }
    }

    // ==================== 自定义通知方法 ====================

    // 打开新增自定义通知弹窗
    const openAddCustomModal = () => {
      editingCustomNotify.value = null
      Object.assign(customForm, {
        id: null,
        name: '',
        enabled: true,
        channel_type: 'wecom_webhook',
        webhook_key: '',
        corp_id: '',
        agent_id: '',
        secret: '',
        to_user: '@all',
        allowed_events: [...defaultEvents],
        allowed_servers: []
      })
      showCustomModal.value = true
    }

    // 打开编辑自定义通知弹窗
    const openEditCustomModal = (notify) => {
      editingCustomNotify.value = notify
      Object.assign(customForm, {
        id: notify.id,
        name: notify.name,
        enabled: notify.enabled,
        channel_type: notify.channel_type,
        webhook_key: notify.webhook_key || '',
        corp_id: notify.corp_id || '',
        agent_id: notify.agent_id || '',
        secret: notify.secret || '',
        to_user: notify.to_user || '@all',
        allowed_events: notify.allowed_events || [...defaultEvents],
        allowed_servers: notify.allowed_servers || []
      })
      showCustomModal.value = true
    }

    // 关闭自定义通知弹窗
    const closeCustomModal = () => {
      showCustomModal.value = false
      editingCustomNotify.value = null
    }

    // 保存自定义通知
    const saveCustomNotify = async () => {
      // 验证通知名称
      if (!customForm.name || customForm.name.trim() === '') {
        customSaveSuccess.value = false
        customSaveMessage.value = '请输入通知名称'
        return
      }
      
      // 根据渠道类型验证必填项
      if (customForm.channel_type === 'wecom_webhook') {
        if (!customForm.webhook_key || customForm.webhook_key.trim() === '') {
          customSaveSuccess.value = false
          customSaveMessage.value = '请输入 Webhook Key'
          return
        }
      } else if (customForm.channel_type === 'wecom_app') {
        if (!customForm.corp_id || customForm.corp_id.trim() === '') {
          customSaveSuccess.value = false
          customSaveMessage.value = '请输入 CorpID'
          return
        }
        if (!customForm.agent_id || customForm.agent_id.trim() === '') {
          customSaveSuccess.value = false
          customSaveMessage.value = '请输入 AgentID'
          return
        }
        if (!customForm.secret || customForm.secret.trim() === '') {
          customSaveSuccess.value = false
          customSaveMessage.value = '请输入 Secret'
          return
        }
      }
      
      customSaving.value = true
      customSaveSuccess.value = false
      customSaveMessage.value = ''
      
      try {
        const isEdit = !!editingCustomNotify.value
        const url = isEdit ? `/api/config/notify/custom/${editingCustomNotify.value.id}` : '/api/config/notify/custom'
        const method = isEdit ? 'PUT' : 'POST'
        
        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({...customForm})
        })
        
        const data = await res.json()
        
        if (data.success) {
          await loadCustomNotifies()
          customSaveSuccess.value = true
          customSaveMessage.value = '保存成功'
          setTimeout(() => {
            closeCustomModal()
            customSaveSuccess.value = false
            customSaveMessage.value = ''
          }, 800)
        } else {
          customSaveSuccess.value = false
          customSaveMessage.value = data.message || '保存失败'
        }
      } catch (error) {
        console.error('保存自定义通知出错:', error)
        customSaveSuccess.value = false
        customSaveMessage.value = '保存失败'
      } finally {
        customSaving.value = false
      }
    }

    // 删除自定义通知
    const deleteCustomNotify = async (notify) => {
      if (!confirm(`确定要删除通知 "${notify.name}" 吗？`)) {
        return
      }
      
      try {
        const res = await fetch(`/api/config/notify/custom/${notify.id}`, {
          method: 'DELETE'
        })
        const data = await res.json()
        
        if (data.success) {
          await loadCustomNotifies()
        } else {
          alert(data.message || '删除失败')
        }
      } catch (error) {
        console.error('删除自定义通知出错:', error)
        alert('删除失败')
      }
    }

    // 切换自定义通知启用状态
    const toggleCustomNotify = async (notify) => {
      try {
        const res = await fetch(`/api/config/notify/custom/${notify.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...notify,
            enabled: notify.enabled
          })
        })
        const data = await res.json()
        
        if (!data.success) {
          notify.enabled = !notify.enabled
          alert(data.message || '更新失败')
        }
      } catch (error) {
        console.error('更新自定义通知状态出错:', error)
        notify.enabled = !notify.enabled
        alert('更新失败')
      }
    }

    // 测试自定义通知
    const testCustomNotify = async (notify) => {
      if (notify.channel_type === 'wecom_app' && (!notify.corp_id || !notify.secret)) {
        alert('请先配置企业微信应用')
        openEditCustomModal(notify)
        return
      }
      if (notify.channel_type === 'wecom_webhook' && !notify.webhook_key) {
        alert('请先配置 Webhook Key')
        openEditCustomModal(notify)
        return
      }
      
      notify.testing = true
      try {
        const response = await fetch(`/api/config/notify/custom/${notify.id}/test`, {
          method: 'POST'
        })
        const data = await response.json()
        alert(data.success ? '测试消息发送成功' : `发送失败: ${data.message}`)
      } catch (error) {
        alert('测试失败')
      } finally {
        notify.testing = false
      }
    }

    // 测试自定义通知表单
    const testCustomForm = async () => {
      customTesting.value = true
      try {
        // 临时创建一个测试配置
        const testConfig = {...customForm}
        
        if (testConfig.channel_type === 'wecom_webhook') {
          if (!testConfig.webhook_key) {
            alert('请先配置 Webhook Key')
            return
          }
          // 直接发送测试
          const response = await fetch('/api/config/notify/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              channel: 'wecom_webhook',
              webhook_key: testConfig.webhook_key
            })
          })
          const data = await response.json()
          alert(data.success ? '测试消息发送成功' : `发送失败: ${data.message}`)
        } else {
          alert('企业微信应用测试请先保存配置')
        }
      } catch (error) {
        alert('测试失败')
      } finally {
        customTesting.value = false
      }
    }

    // 打开自定义通知事件弹窗
    const openCustomEventsModal = async (notify) => {
      eventsCustomNotify.value = notify
      eventsChannel.value = null
      await loadAvailableEvents()
      selectedEvents.value = notify.allowed_events || [...defaultEvents]
      showEventsModal.value = true
    }

    // 打开自定义通知服务器过滤弹窗
    const showServersModal = ref(false)
    const serversCustomNotify = ref(null)
    const serversTargetName = ref('')
    const selectedServers = ref([])
    const openCustomServersModal = (notify) => {
      serversCustomNotify.value = notify
      serversTargetName.value = notify.name || '通知'
      selectedServers.value = notify.allowed_servers || []
      showServersModal.value = true
    }
    const saveCustomServers = async () => {
      if (!serversCustomNotify.value) return
      const notify = serversCustomNotify.value
      const payload = {
        name: notify.name,
        enabled: notify.enabled,
        channel_type: notify.channel_type,
        webhook_key: notify.webhook_key || '',
        corp_id: notify.corp_id || '',
        agent_id: notify.agent_id || '',
        secret: notify.secret || '',
        to_user: notify.to_user || '@all',
        allowed_events: notify.allowed_events || [...defaultEvents],
        allowed_servers: [...selectedServers.value]
      }
      try {
        const res = await fetch(`/api/config/notify/custom/${encodeURIComponent(notify.id)}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        const data = await res.json()
        if (data.success) {
          notify.allowed_servers = [...selectedServers.value]
          showServersModal.value = false
          customSaveMessage.value = '服务器过滤已保存'
          customSaveSuccess.value = true
          setTimeout(() => { customSaveMessage.value = '' }, 2000)
        } else {
          alert('保存失败：' + (data.message || '未知错误'))
        }
      } catch (e) {
        alert('保存失败：' + e.message)
      }
    }

    onMounted(() => {
      loadCustomNotifies()
      loadEmbyServers()
    })

    return {
      showEventsModal,
      eventsCustomNotify,
      eventsChannel,
      saving,
      loadingEvents,
      availableEvents,
      selectedEvents,
      saveSuccess,
      saveMessage,
      closeEventsModal,
      saveEventsConfig,
      selectAllEvents,
      deselectAllEvents,
      resetDefaultEvents,
      // 自定义通知
      customNotifies,
      customForm,
      embyServers,
      customSaving,
      customTesting,
      customSaveSuccess,
      customSaveMessage,
      showCustomModal,
      editingCustomNotify,
      openAddCustomModal,
      openEditCustomModal,
      closeCustomModal,
      saveCustomNotify,
      deleteCustomNotify,
      toggleCustomNotify,
      testCustomNotify,
      testCustomForm,
      openCustomEventsModal,
      showServersModal,
      serversTargetName,
      selectedServers,
      openCustomServersModal,
      saveCustomServers,
      embyServers
    }
  }
}
</script>

<style scoped>
/* 通知渠道列表 */
.notify-channels {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

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

.empty-custom-notify {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-color);
}

.channel-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.channel-item:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.channel-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.channel-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.channel-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.channel-name {
  font-weight: 500;
  color: var(--text-primary);
}

.channel-type {
  font-size: 12px;
  color: var(--text-tertiary);
}

.channel-status {
  font-size: 12px;
  color: var(--text-tertiary);
}

.channel-status.active {
  color: var(--success-color);
}

.channel-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.channel-actions .btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

/* 通知卡片按钮上的数量徽标 */
.badge {
  margin-left: 4px;
  padding: 1px 7px;
  font-size: 11px;
  line-height: 1.4;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.25);
  color: inherit;
  white-space: nowrap;
}

/* 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
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
  transition: var(--transition-fast);
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: var(--transition-fast);
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--success-color);
}

input:checked + .slider:before {
  transform: translateX(20px);
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
  padding: var(--spacing-md);
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 500px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}

.modal-content.events-modal {
  max-width: 600px;
  max-height: 80vh;
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
  font-weight: 600;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-tertiary);
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.btn-close:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

/* 表单样式 */
.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--text-secondary);
  font-size: 14px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
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

/* 服务器过滤多选样式 */
.server-filter {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  max-height: 200px;
  overflow-y: auto;
  padding: var(--spacing-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.server-checkbox {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 6px var(--spacing-sm);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.server-checkbox:hover {
  background: var(--bg-tertiary);
}

.server-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.server-name {
  font-weight: 500;
  color: var(--text-primary);
}

.server-url {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 事件选择样式 */
.events-loading {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-tertiary);
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  max-height: 50vh;
  overflow-y: auto;
  padding-right: var(--spacing-sm);
}

.event-category {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.category-header {
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--border-color);
}

.category-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.category-events {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding-left: var(--spacing-sm);
}

.event-checkbox {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 2px solid transparent;
}

.event-checkbox:hover {
  background: var(--bg-tertiary);
}

.event-checkbox.checked {
  border-color: var(--primary-color);
  background: rgba(59, 130, 246, 0.1);
}

.event-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.event-emoji {
  font-size: 18px;
}

.event-name {
  flex: 1;
  font-weight: 500;
  color: var(--text-primary);
}

.event-type {
  font-size: 12px;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.events-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-right: auto;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--border-color);
}

.btn-info {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
}

.btn-info:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
}

.btn-danger {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error-color);
}

.btn-danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.2);
}

.btn-text {
  background: transparent;
  color: var(--text-secondary);
}

.btn-text:hover:not(:disabled) {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

/* 保存状态提示 */
.save-status {
  font-size: 14px;
  margin-right: auto;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
}

.save-status.success {
  color: var(--success-color);
  background: rgba(34, 197, 94, 0.1);
}

.save-status.error {
  color: var(--error-color);
  background: rgba(239, 68, 68, 0.1);
}
</style>