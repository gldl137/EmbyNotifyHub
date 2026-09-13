import { createRouter, createWebHistory } from 'vue-router'
import Events from '../views/Events.vue'
import MediaSettings from '../views/MediaSettings.vue'
import SystemSettings from '../views/SystemSettings.vue'
import About from '../views/About.vue'

const routes = [
  {
    path: '/',
    redirect: '/events'
  },
  {
    path: '/events',
    name: 'Events',
    component: Events,
    meta: { title: '通知事件', icon: '📋' }
  },
  {
    path: '/media-settings',
    name: 'MediaSettings',
    component: MediaSettings,
    meta: { title: '媒体设置', icon: '🎬' }
  },
  {
    path: '/system-settings',
    name: 'SystemSettings',
    component: SystemSettings,
    meta: { title: '系统设置', icon: '⚙️' }
  },
  {
    path: '/about',
    name: 'About',
    component: About,
    meta: { title: '关于', icon: 'ℹ️' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
