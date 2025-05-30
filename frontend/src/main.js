import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './assets/styles/global.scss'

console.log('开始初始化 analyDesign 应用...')

// 检查必要的元素是否存在
const appElement = document.getElementById('app')
if (!appElement) {
  console.error('找不到 #app 元素')
} else {
  console.log('找到 #app 元素:', appElement)
}

try {
  console.log('创建Vue应用实例...')
  const app = createApp(App)

  console.log('注册 Element Plus 图标...')
  // 注册 Element Plus 图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  console.log('配置Pinia...')
  app.use(createPinia())
  
  console.log('配置路由...')
  app.use(router)
  
  console.log('配置Element Plus...')
  // 暂时不配置locale，使用默认设置
  app.use(ElementPlus)

  // 全局错误处理
  app.config.errorHandler = (err, vm, info) => {
    console.error('Vue应用错误:', err, info)
  }

  console.log('挂载应用到 #app...')
  app.mount('#app')
  console.log('analyDesign 应用初始化完成！')
  
  // 验证应用是否成功挂载
  setTimeout(() => {
    const appContent = document.getElementById('app').innerHTML
    if (appContent.includes('正在加载')) {
      console.error('应用挂载失败，仍显示加载状态')
    } else {
      console.log('应用成功挂载，内容已更新')
    }
  }, 1000)
  
} catch (error) {
  console.error('应用初始化失败:', error)
  console.error('错误堆栈:', error.stack)
  
  // 显示错误信息
  const appElement = document.getElementById('app')
  if (appElement) {
    appElement.innerHTML = `
      <div style="padding: 20px; color: white; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;">
        <h2>应用启动失败</h2>
        <p>错误信息: ${error.message}</p>
        <p>请检查浏览器控制台获取详细信息</p>
        <div style="margin-top: 20px; text-align: left; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 5px; max-width: 600px;">
          <pre style="color: #ffcccc; font-size: 12px; white-space: pre-wrap;">${error.stack}</pre>
        </div>
      </div>
    `
  }
} 