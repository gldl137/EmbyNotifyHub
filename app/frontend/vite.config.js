import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 测试阶段通过容器名访问后端 (python-cs 为后端容器服务名, 端口 7000)
// 可用环境变量 VITE_PROXY_TARGET 覆盖, 默认 http://python-cs:7000
const API_TARGET = process.env.VITE_PROXY_TARGET || 'http://python-cs:7000'

export default defineConfig(({ command }) => {
  // 仅 dev (serve) 阶段把代理目标注入前端并显示; 生产构建不注入调试文本
  const isDev = command === 'serve'

  if (isDev) {
    // 启动日志打印当前连接的后端地址, 方便排查代理是否指向正确容器
    console.log(`[EmbyNotifyHub] 前端代理后端地址: ${API_TARGET}`)
  }

  return {
    plugins: [vue()],
    base: './',  // 使用相对路径，解决静态资源404问题
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    // 仅 dev 阶段注入, 供前端界面显示当前连接的后端地址; 生产不注入
    define: isDev
      ? { 'import.meta.env.VITE_API_TARGET': JSON.stringify(API_TARGET) }
      : {},
    build: {
      outDir: '../backend/static',
      emptyOutDir: true,
    },
    server: {
      port: 5173,
      proxy: {
        '/webhook': API_TARGET,
        '/health': API_TARGET,
        '/api': API_TARGET,
      }
    }
  }
})
