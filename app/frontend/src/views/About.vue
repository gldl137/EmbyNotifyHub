<template>
  <div class="about page-container">
    <header class="page-header">
      <h2 class="page-title">
        <span class="icon">ℹ️</span>
        关于
      </h2>
      <p class="page-desc">项目信息</p>
    </header>

    <div class="about-content">
      <div class="info-card">
        <!-- 头部：图标 + 名称/版本 -->
        <div class="card-header">
          <div class="app-icon">📺</div>
          <div class="app-info">
            <h3 class="app-name">{{ aboutInfo.project_name || 'EmbyNotifyHub' }}</h3>
            <span class="app-version">v{{ aboutInfo.version || '1.0.0' }}</span>
          </div>
        </div>

        <!-- 信息网格 -->
        <div class="info-grid">
          <div class="info-item">
            <span class="info-icon">👤</span>
            <div class="info-content">
              <span class="info-label">开发者</span>
              <span class="info-value">{{ aboutInfo.developer || 'EmbyNotifyHub Contributors' }}</span>
            </div>
          </div>
        </div>

        <!-- 功能特性 -->
        <div class="features-box" v-if="aboutInfo.features && aboutInfo.features.length > 0">
          <div class="features-title">✨ 功能特性</div>
          <div class="features-tags">
            <span v-for="(feature, index) in aboutInfo.features" :key="index" class="feature-tag">
              {{ feature }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { getAboutInfo } from '@/api'

export default {
  name: 'About',
  setup() {
    const aboutInfo = ref({})

    const loadAboutInfo = async () => {
      try {
        const res = await getAboutInfo()
        if (res.success && res.data) {
          aboutInfo.value = res.data
        }
      } catch (error) {
        console.error('加载关于信息失败:', error)
      }
    }

    onMounted(() => {
      loadAboutInfo()
    })

    return {
      aboutInfo
    }
  }
}
</script>

<style scoped>
.about-content {
  max-width: 1000px;
  width: 100%;
}

.info-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 32px;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* 头部区域 - 水平排列 */
.card-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.app-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  box-shadow: 0 4px 12px rgba(var(--primary-rgb), 0.3);
}

.app-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.app-name {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.app-version {
  font-size: 14px;
  color: var(--text-secondary);
  background: var(--bg-hover);
  padding: 4px 12px;
  border-radius: 20px;
  width: fit-content;
}

/* 信息网格 - 水平排列 */
.info-grid {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-hover);
  padding: 12px 20px;
  border-radius: 12px;
  flex: 1;
}

.info-icon {
  font-size: 20px;
  width: 36px;
  height: 36px;
  background: var(--bg-card);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 600;
}

/* 功能特性 - 标签云形式 */
.features-box {
  background: var(--bg-hover);
  border-radius: 12px;
  padding: 20px;
}

.features-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  font-weight: 500;
}

.features-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-tag {
  background: var(--bg-card);
  color: var(--text-primary);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.feature-tag:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}
</style>
