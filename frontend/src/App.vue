<template>
  <div id="app">
    <div v-if="hasError" class="error-container">
      <h2>应用启动遇到问题</h2>
      <p>{{ errorMessage }}</p>
      <el-button @click="retryInit" type="primary">重试</el-button>
    </div>
    <router-view v-else />
  </div>
</template>

<script setup>
import { ref, onMounted, onErrorCaptured } from 'vue'
import { useWebSocketStore } from './stores/websocket'

const hasError = ref(false)
const errorMessage = ref('')
const wsStore = useWebSocketStore()

const retryInit = () => {
  hasError.value = false
  errorMessage.value = ''
  initApp()
}

const initApp = () => {
  try {
    // 初始化 WebSocket 连接（使用模拟模式）
    wsStore.connect()
    console.log('应用初始化完成')
  } catch (error) {
    console.error('应用初始化失败:', error)
    hasError.value = true
    errorMessage.value = error.message
  }
}

onMounted(() => {
  initApp()
})

// 捕获子组件错误
onErrorCaptured((error, instance, info) => {
  console.error('组件错误:', error, info)
  hasError.value = true
  errorMessage.value = `组件错误: ${error.message}`
  return false
})
</script>

<style lang="scss">
#app {
  height: 100vh;
  overflow: hidden;
}

.error-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
  padding: 20px;

  h2 {
    margin-bottom: 16px;
  }

  p {
    margin-bottom: 20px;
    max-width: 600px;
  }
}
</style> 