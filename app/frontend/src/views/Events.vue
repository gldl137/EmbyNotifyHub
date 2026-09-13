<template>
  <div class="events page-container">
    <!-- 通知事件列表 -->
    <div class="card events-card">
      <div class="card-header">
        <h3 class="card-title">
          <span class="icon">📋</span>
          通知事件
        </h3>
        <div class="filters">
          <button class="btn btn-secondary" @click="refreshEvents">
            <span class="icon">🔄</span> 刷新
          </button>
          <button class="btn btn-danger" @click="clearEvents">
            <span class="icon">🗑️</span> 清空
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <span class="spinner"></span>
        加载中...
      </div>

      <div v-else-if="events.length === 0" class="empty-state">
        <span class="empty-icon">📭</span>
        <p>暂无通知事件</p>
        <span class="empty-hint">当 Emby 有事件发生时，会显示在这里<br>请先在「媒体设置 → Emby配置」中配置 Webhook</span>
      </div>

      <div v-else class="events-list">
        <div 
          v-for="event in events" 
          :key="event.id" 
          class="event-item"
          :class="event.eventType"
        >
          <!-- 事件头部：类型和操作按钮 -->
          <div class="event-header-row">
            <span class="event-type-label-inline">事件：{{ event.eventType }}</span>
            <div class="action-right">
              <a
                v-if="event.doubanUrl"
                :href="event.doubanUrl"
                target="_blank"
                class="btn btn-link"
              >
                豆瓣
              </a>
              <a
                v-if="event.tmdbUrl"
                :href="event.tmdbUrl"
                target="_blank"
                class="btn btn-link"
              >
                TMDB
              </a>
              <a
                v-if="event.imdbUrl"
                :href="event.imdbUrl"
                target="_blank"
                class="btn btn-link"
              >
                IMDB
              </a>
              <!-- 各渠道发送状态 -->
              <div v-if="event.channelResults && Object.keys(event.channelResults).length > 0" class="channel-results">
                <span 
                  v-for="(result, id) in event.channelResults" 
                  :key="id"
                  class="channel-status"
                  :class="{ 
                    'success': result.success === true, 
                    'failed': result.success === false,
                    'disabled': result.success === null && result.reason === 'disabled',
                    'filtered': result.success === null && result.reason === 'filtered'
                  }"
                >
                  {{ result.name || '通知' }}
                </span>
              </div>
              <span v-else class="status-badge" :class="event.status">
                {{ getStatusText(event.status) }}
              </span>
            </div>
          </div>
          
          <!-- 事件主体：封面 + 内容 -->
          <div class="event-body">
            <div
              v-if="event.seriesPoster || event.poster"
              class="event-poster"
            >
              <img :src="event.seriesPoster || event.poster" :alt="event.title" />
            </div>
            <div class="event-poster placeholder system" v-else-if="event.mediaType === 'System'">
              <span>⚙️</span>
            </div>
            <div
              v-else
              class="event-poster placeholder"
            >
              <span>🎬</span>
            </div>
            
            <div class="event-content">
            <!-- 事件标题（使用通知标题，与发送的通知一致） -->
            <h4 class="event-series" :class="{ system: event.mediaType === 'System' }">
              {{ event.messageTitle || event.title }}
            </h4>
            
            <!-- 事件内容（使用通知内容，与发送的通知一致） -->
            <pre class="event-content-text" v-if="event.messageContent">{{ event.messageContent }}</pre>
            
            <!-- 备用：如果没有通知内容，显示原有元数据 -->
            <div class="event-meta" v-else>
              <span v-if="event.year" class="meta-item">
                <span class="icon">📅</span> {{ event.year }}
              </span>
              <span v-if="event.mediaType" class="meta-item">
                <span class="icon">{{ getMediaTypeIcon(event.mediaType) }}</span> {{ formatMediaType(event.mediaType) }}
              </span>
              <span v-if="event.userName" class="meta-item">
                <span class="icon">👤</span> {{ event.userName }}
              </span>
              <!-- 播放进度 -->
              <span v-if="event.playPosition != null && event.playDuration != null && event.playDuration > 0" class="meta-item progress">
                <span class="icon">⏱️</span>
                播放进度：{{ formatProgress(event.playPosition, event.playDuration) }}
              </span>
              <!-- 客户端和设备 -->
              <span v-if="event.client || event.deviceName" class="meta-item">
                <span class="icon">📱</span> {{ formatClient(event.client, event.deviceName) }}
              </span>
              <!-- 视频规格 (4K/HDR/10bit等) -->
              <span v-if="event.displayTitle || event.videoRange || event.bitDepth" class="meta-item">
                <span class="icon">🎬</span> {{ formatVideoSpec(event) }}
              </span>
              <!-- 入库集数（多集入库时显示） -->
              <span v-if="event.eventType === 'library.new' && event.episodeCount && event.episodeCount > 1" class="meta-item">
                <span class="icon">📦</span> 入库 {{ event.episodeCount }} 集
                <span v-if="event.episodeRange" class="episode-range">({{ event.episodeRange }})</span>
              </span>
            </div>
            
            <p class="event-overview" v-if="!event.messageContent && event.overview">
              {{ event.overview }}
            </p>
            </div>  <!-- event-content -->
          </div>    <!-- event-body -->
        </div>      <!-- event-item -->
      </div>      <!-- events-list -->
      
      <!-- 分页 -->
      <div v-if="total > 0" class="pagination">
        <div class="pagination-info">
          共 {{ total }} 条，第 {{ currentPage }} / {{ totalPages }} 页
        </div>
        <div class="pagination-btns">
          <button 
            class="btn btn-sm" 
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            上一页
          </button>
          <button 
            v-for="page in visiblePages" 
            :key="page"
            class="btn btn-sm"
            :class="{ 'btn-primary': page === currentPage }"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
          <button 
            class="btn btn-sm" 
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

export default {
  name: 'Events',
  setup() {
    const events = ref([])
    const loading = ref(false)
    
    // 分页
    const currentPage = ref(1)
    const pageSize = ref(5)
    const total = ref(0)
    
    // 计算总页数
    const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
    
    // 显示的页码
    const visiblePages = computed(() => {
      const pages = []
      const maxVisible = 5
      let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
      let end = Math.min(totalPages.value, start + maxVisible - 1)
      
      if (end - start < maxVisible - 1) {
        start = Math.max(1, end - maxVisible + 1)
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    })

    // 格式化时间
    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date
      
      // 1分钟内
      if (diff < 60000) return '刚刚'
      // 1小时内
      if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
      // 24小时内
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
      
      return date.toLocaleString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    // 格式化媒体类型
    const formatMediaType = (type) => {
      const typeMap = {
        'Movie': '电影',
        'Series': '剧集',
        'Episode': '单集',
        'Season': '季',
        'System': '系统',
        'Audio': '音乐'
      }
      return typeMap[type] || type
    }

    // 获取媒体类型图标
    const getMediaTypeIcon = (type) => {
      const iconMap = {
        'Movie': '🎬',
        'Series': '📺',
        'Episode': '📺',
        'Audio': '🎵',
        'System': '⚙️'
      }
      return iconMap[type] || '🎭'
    }

    // 格式化状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'pending': '处理中',
        'sent': '已发送',
        'success': '成功',
        'failed': '失败',
        'filtered': '已过滤',
        'skipped': '已跳过',
        'processing': '处理中'
      }
      return statusMap[status] || status
    }

    // 格式化播放进度 (ticks -> 时分秒)
    const formatProgress = (position, duration) => {
      // ticks 转换: 1 tick = 100 nanoseconds = 0.0001 milliseconds
      const positionSec = Math.floor(position / 10000000)
      const durationSec = Math.floor(duration / 10000000)
      
      const formatTime = (seconds) => {
        const h = Math.floor(seconds / 3600)
        const m = Math.floor((seconds % 3600) / 60)
        const s = seconds % 60
        if (h > 0) {
          return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
        }
        return `${m}:${String(s).padStart(2, '0')}`
      }
      
      return `${formatTime(positionSec)} / ${formatTime(durationSec)}`
    }

    // 格式化客户端和设备信息
    const formatClient = (client, deviceName) => {
      if (client && deviceName) {
        return `${client} · ${deviceName}`
      }
      return client || deviceName || ''
    }

    // 格式化视频规格 (4K/HDR/10bit等)
    const formatVideoSpec = (event) => {
      const displayTitle = event.displayTitle || ''
      
      // 优先使用 displayTitle，因为它包含完整信息（分辨率、HDR、编码格式等）
      if (displayTitle) {
        return displayTitle
      }
      
      const specs = []

      // 分辨率判断 (4K/1080p等) - 根据宽度或高度判断（放宽标准，考虑实际视频可能裁剪黑边）
      const width = event.width || 0
      const height = event.height || 0
      // 4K: >= 3800x2100（标准3840x2160，允许小幅裁剪）
      if (width >= 3800 || height >= 2100) {
        specs.push('4K')
      // 2K: >= 2500x1400（标准2560x1440，允许小幅裁剪）
      } else if (width >= 2500 || height >= 1400) {
        specs.push('2K')
      // 1080p: >= 1900x1000（标准1920x1080，允许小幅裁剪）
      } else if (width >= 1900 || height >= 1000) {
        specs.push('1080p')
      // 720p: >= 1200x700
      } else if (width >= 1200 || height >= 700) {
        specs.push('720p')
      }
      
      // HDR/SDR
      if (event.videoRange) {
        if (event.videoRange.toLowerCase().includes('hdr')) {
          specs.push('HDR')
        } else if (event.videoRange.toLowerCase().includes('sdr')) {
          specs.push('SDR')
        } else {
          specs.push(event.videoRange)
        }
      }
      
      // 位深
      if (event.bitDepth) {
        specs.push(`${event.bitDepth}bit`)
      }
      
      return specs.join(' · ') || ''
    }

    // 获取事件列表
    const fetchEvents = async () => {
      loading.value = true
      try {
        const params = new URLSearchParams()
        params.append('page', currentPage.value)
        params.append('page_size', pageSize.value)
        
        const response = await fetch(`/api/events/query/list?${params}`)
        const data = await response.json()
        if (data.success) {
          events.value = data.data || []
          total.value = data.total || 0
        }
      } catch (error) {
        console.error('获取事件失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    // 跳转到指定页
    const goToPage = (page) => {
      if (page < 1 || page > totalPages.value) return
      currentPage.value = page
      fetchEvents()
    }

    // 刷新
    const refreshEvents = () => {
      currentPage.value = 1
      fetchEvents()
    }

    // 清空事件
    const clearEvents = async () => {
      if (!confirm('确定要清空所有事件记录吗？')) return
      try {
        const response = await fetch('/api/events/manage/clear/all', { method: 'DELETE' })
        const data = await response.json()
        console.log('清空响应:', data)
        if (data.success) {
          events.value = []
          total.value = 0
          currentPage.value = 1
          // 强制刷新确认已清空
          setTimeout(() => fetchEvents(), 500)
        } else {
          alert('清空失败: ' + (data.message || '未知错误'))
        }
      } catch (error) {
        console.error('清空事件失败:', error)
        alert('清空失败: ' + error.message)
      }
    }

    // SSE 连接
    let eventSource = null
    let refreshTimeout = null
    let pendingRefresh = false
    
    // 防抖刷新 - 避免频繁刷新列表
    const debouncedRefresh = () => {
      // 如果已经在第一页，使用防抖
      if (currentPage.value === 1) {
        pendingRefresh = true
        // 清除之前的定时器
        if (refreshTimeout) {
          clearTimeout(refreshTimeout)
        }
        // 2秒后刷新
        refreshTimeout = setTimeout(() => {
          if (pendingRefresh) {
            fetchEvents()
            pendingRefresh = false
          }
        }, 2000)
      } else {
        // 不在第一页，不自动刷新，显示提示
        console.log('有新事件，但不在第一页，不自动刷新')
      }
    }
    
    const connectSSE = () => {
      if (eventSource) {
        eventSource.close()
      }
      
      eventSource = new EventSource('/api/events/stream')
      
      eventSource.onmessage = (event) => {
        // 忽略心跳
        if (!event.data || event.data === ': heartbeat') return
        
        try {
          const data = JSON.parse(event.data)
          console.log('SSE 收到消息:', data)
          
          if (data.type === 'new_event') {
            // 有新事件，使用防抖刷新
            console.log('有新事件，准备刷新列表:', data.data)
            debouncedRefresh()
          }
        } catch (e) {
          console.error('解析 SSE 消息失败:', e)
        }
      }
      
      eventSource.onopen = () => {
        console.log('SSE 连接已建立')
      }
      
      eventSource.onerror = (error) => {
        console.error('SSE 连接错误:', error)
        // 5秒后重连
        setTimeout(() => {
          console.log('尝试重新连接 SSE...')
          connectSSE()
        }, 5000)
      }
    }
    
    const disconnectSSE = () => {
      if (eventSource) {
        eventSource.close()
        eventSource = null
        console.log('SSE 连接已断开')
      }
      // 清理刷新定时器
      if (refreshTimeout) {
        clearTimeout(refreshTimeout)
        refreshTimeout = null
      }
      pendingRefresh = false
    }

    onMounted(() => {
      // 页面加载时获取一次事件列表
      fetchEvents()
      // 建立 SSE 连接
      connectSSE()
    })
    
    onUnmounted(() => {
      // 页面卸载时断开 SSE 连接
      disconnectSSE()
    })

    return {
      events,
      loading,
      currentPage,
      pageSize,
      total,
      totalPages,
      visiblePages,
      formatTime,
      formatMediaType,
      getMediaTypeIcon,
      formatProgress,
      formatClient,
      formatVideoSpec,
      getStatusText,
      refreshEvents,
      clearEvents,
      goToPage
    }
  }
}
</script>

<style scoped>
.events {
  max-width: 1000px;
  width: 100%;
}

/* 事件列表 */
.events-card {
  min-height: 400px;
}

.events-card .filters {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.event-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--border-color);
  transition: all var(--transition-fast);
}

.event-header-row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding: 0 var(--spacing-xs);
}

.event-header-row .event-type-label-inline {
  font-size: 12px;
  color: var(--text-tertiary);
}

.event-header-row .action-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

/* 各通知渠道状态 */
.channel-results {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  align-items: center;
}

.channel-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  white-space: nowrap;
}

.channel-status.success {
  background: var(--success-light);
  color: var(--success-color);
}

.channel-status.failed {
  background: var(--error-light);
  color: var(--error-color);
}

.channel-status.disabled {
  background: var(--border-light);
  color: var(--text-tertiary);
}

.channel-status.filtered {
  background: var(--info-light);
  color: var(--info-color);
}

.event-body {
  display: flex;
  flex-direction: row;
  gap: var(--spacing-md);
}

.event-item:hover {
  background: var(--bg-hover);
  transform: translateX(4px);
}

.event-item.library\.new {
  border-left-color: var(--success-color);
}

.event-item.library\.deleted,
.event-item.deep\.delete {
  border-left-color: var(--error-color);
}

.event-item.playback\.start {
  border-left-color: var(--primary-color);
}

.event-item.playback\.pause {
  border-left-color: var(--info-color);
}

.event-item.playback\.stop {
  border-left-color: var(--warning-color);
}

.event-poster {
  width: 80px;
  height: 120px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--bg-white);
  display: block;
  text-decoration: none;
}

.event-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.event-poster.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--border-color);
  font-size: 32px;
}

.event-content {
  flex: 1;
  min-width: 0;
}

.event-content .event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.event-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.event-badge.library\.new {
  background: var(--success-light);
  color: var(--success-color);
}

.event-badge.library\.deleted,
.event-badge.deep\.delete {
  background: var(--error-light);
  color: var(--error-color);
}

.event-badge.playback\.start {
  background: var(--primary-light);
  color: var(--primary-color);
}

.event-badge.playback\.pause {
  background: var(--info-light);
  color: var(--info-color);
}

.event-badge.playback\.stop {
  background: var(--warning-light);
  color: var(--warning-color);
}

.event-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.event-series {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 var(--spacing-xs) 0;
  padding: 0 var(--spacing-md);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.event-content-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  background: var(--bg-secondary);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  max-height: 120px;
  overflow-y: auto;
}

.event-series .episode-info {
  font-size: 12px;
  font-weight: 500;
  color: var(--primary-color);
  background: var(--primary-light);
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.event-series .episode-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.event-series.system {
  color: var(--text-secondary);
  font-size: 14px;
}

.event-poster.placeholder.system {
  background: var(--info-light);
  color: var(--info-color);
}

.event-meta {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  padding: 0 var(--spacing-md);
  flex-wrap: wrap;
}

.meta-item {
  font-size: 13px;
  color: var(--text-secondary);
}

.meta-item.progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.episode-range {
  color: var(--text-tertiary);
  font-size: 12px;
  margin-left: 2px;
}

.event-overview {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
  padding: 0 var(--spacing-md);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 分页样式 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) 0;
  border-top: 1px solid var(--border-color);
  margin-top: var(--spacing-md);
}

.pagination-info {
  font-size: 14px;
  color: var(--text-secondary);
}

.pagination-btns {
  display: flex;
  gap: var(--spacing-xs);
}

.pagination-btns .btn {
  min-width: 36px;
  padding: 6px 12px;
}

.pagination-btns .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .event-item {
    flex-direction: column;
  }

  .event-header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }

  .event-header-row .action-right {
    width: 100%;
    justify-content: flex-start;
  }

  .event-body {
    flex-direction: column;
  }

  .event-poster {
    width: auto;
    max-width: 100%;
    height: auto;
    align-self: center;
  }

  .event-poster img {
    width: auto;
    max-width: 100%;
    height: auto;
    display: block;
  }

  .events-card .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .events-card .filters {
    width: 100%;
  }
  
  .pagination {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
  
  .pagination-info {
    font-size: 12px;
  }
}
</style>
