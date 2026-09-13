<template>
  <div class="app">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-icon">📺</span>
        <h1>EmbyNotifyHub</h1>
      </div>
      
      <nav class="nav">
        <router-link 
          v-for="route in routes" 
          :key="route.path"
          :to="route.path"
          class="nav-item"
          :class="{ active: $route.path === route.path }"
        >
          <span class="nav-icon">{{ route.meta?.icon }}</span>
          <span class="nav-title">{{ route.meta?.title }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="status-indicator" :class="healthStatus">
          <span class="status-dot"></span>
          {{ healthText }}
        </div>
        <!-- 仅测试阶段(dev)显示后端连接地址, 生产不显示 -->
        <div class="api-target" v-if="showApiTarget">
          后端地址: {{ apiTarget }}
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import router from './router'

export default {
  name: 'App',
  setup() {
    const route = useRoute()
    const healthStatus = ref('unknown')
    const healthText = ref('检查中...')
    // 仅测试阶段(dev)显示连接地址: 由 vite define 注入 VITE_API_TARGET, 取不到则回退同源
    const isDev = import.meta.env.DEV
    const showApiTarget = ref(isDev)
    const apiTarget = ref(
      (import.meta.env && import.meta.env.VITE_API_TARGET) || window.location.origin
    )
    if (isDev) {
      console.log('[EmbyNotifyHub] 前端连接后端地址:', apiTarget.value)
    }

    // 获取路由列表（排除重定向）
    const routes = computed(() => {
      return router.getRoutes().filter(r => !r.redirect && r.meta?.title)
    })

    // 检查服务状态
    const checkHealth = async () => {
      try {
        const response = await fetch('/health')
        const data = await response.json()
        if (data.status === 'healthy') {
          healthStatus.value = 'online'
          healthText.value = '服务正常'
        } else {
          healthStatus.value = 'error'
          healthText.value = '服务异常'
        }
      } catch (error) {
        healthStatus.value = 'offline'
        healthText.value = '服务离线'
      }
    }

    onMounted(() => {
      checkHealth()
      // 每30秒检查一次
      setInterval(checkHealth, 30000)
    })

    return {
      routes,
      healthStatus,
      healthText,
      apiTarget,
      showApiTarget
    }
  }
}
</script>

<style scoped>
.app {
  display: flex;
  min-height: 100vh;
}

/* 侧边栏 */
.sidebar {
  width: 240px;
  background: var(--bg-sidebar);
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
  z-index: 100;
  border-right: 1px solid var(--border-color);
}

.logo {
  padding: var(--spacing-lg) var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}

.logo-icon {
  font-size: 28px;
}

.logo h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.nav {
  flex: 1;
  padding: var(--spacing-md) 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 14px var(--spacing-lg);
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--transition-fast);
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--primary-color);
}

.nav-item.active {
  background: var(--primary-light);
  color: var(--primary-color);
  border-left-color: var(--primary-color);
}

.nav-icon {
  font-size: 20px;
}

.nav-title {
  font-size: 15px;
  font-weight: 500;
}

.sidebar-footer {
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 13px;
  color: var(--text-tertiary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-tertiary);
}

.status-indicator.online .status-dot {
  background: var(--success-color);
}

.status-indicator.online {
  color: var(--success-color);
}

.status-indicator.offline .status-dot {
  background: var(--error-color);
}

.status-indicator.offline {
  color: var(--error-color);
}

.status-indicator.error .status-dot {
  background: var(--warning-color);
}

.status-indicator.error {
  color: var(--warning-color);
}

.api-target {
  margin-top: var(--spacing-sm);
  font-size: 12px;
  color: var(--text-tertiary);
  word-break: break-all;
  line-height: 1.4;
}

/* 主内容区 */
.main-content {
  flex: 1;
  margin-left: 240px;
  padding: var(--spacing-lg);
  min-height: 100vh;
  background: var(--bg-primary);
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    height: auto;
    position: relative;
  }
  
  .main-content {
    margin-left: 0;
  }
  
  .nav {
    display: flex;
    padding: var(--spacing-sm);
  }
  
  .nav-item {
    flex: 1;
    justify-content: center;
    padding: var(--spacing-sm);
    border-left: none;
    border-bottom: 3px solid transparent;
  }
  
  .nav-item.active {
    border-left: none;
    border-bottom-color: var(--primary-color);
  }
  
  .nav-title {
    display: none;
  }
  
  .sidebar-footer {
    display: none;
  }
  
  .app {
    flex-direction: column;
  }
}
</style>
