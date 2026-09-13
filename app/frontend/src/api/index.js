import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器，直接返回 data
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 健康检查
export const getHealth = () => axios.get('/health')

// 聚合配置 API
export const getAggregationConfig = () => api.get('/config/aggregation')
export const updateAggregationConfig = (data) => api.post('/config/aggregation', data)

// TMDB 配置 API
export const getTmdbConfig = () => api.get('/config/tmdb')
export const updateTmdbConfig = (data) => api.post('/config/tmdb', data)
export const testTmdbConfig = () => api.post('/config/tmdb/test')

// Emby 配置 API
export const getEmbyConfig = () => api.get('/config/emby')
export const updateEmbyConfig = (data) => api.post('/config/emby', data)
export const testEmbyConfig = () => api.post('/config/emby/test')

// 通知配置 API
export const getNotifyConfig = () => api.get('/config/notify')
export const updateNotifyConfig = (data) => api.post('/config/notify', data)
export const testNotifyConfig = () => api.post('/config/notify/test')

// 系统配置 API
export const getSystemConfig = () => api.get('/config/system')
export const updateSystemConfig = (data) => api.post('/config/system', data)

// 事件 API
export const getEvents = (params) => api.get('/events', { params })
export const getEvent = (id) => api.get(`/events/${id}`)
export const deleteEvent = (id) => api.delete(`/events/${id}`)
export const clearEvents = () => api.delete('/events')
export const getEventStats = () => api.get('/events/stats')

// 关于页面 API
export const getAboutInfo = () => api.get('/config/system/about')

export default api
