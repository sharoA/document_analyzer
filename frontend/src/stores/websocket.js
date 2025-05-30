import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8081',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.data)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const useWebSocketStore = defineStore('websocket', () => {
  // 状态
  const isConnected = ref(false)
  const connectionStatus = ref('disconnected')
  const messages = ref([])
  const currentSessionId = ref(null)
  const isProcessing = ref(false)
  const processingSteps = ref([])
  const currentProcessing = ref(null)
  const analysisResult = ref(null)

  // 计算属性
  const lastMessage = computed(() => {
    return messages.value.length > 0 ? messages.value[messages.value.length - 1] : null
  })

  // 连接方法（模拟模式）
  const connect = () => {
    try {
      connectionStatus.value = 'connecting'
      
      // 模拟连接过程
      setTimeout(() => {
        isConnected.value = true
        connectionStatus.value = 'connected'
        console.log('WebSocket 连接成功（模拟模式）')
        
        // 添加欢迎消息
        addMessage({
          type: 'chat_response',
          message: '您好！我是智能需求分析助手，可以帮您分析需求文档。请上传您的文档开始分析，或者直接与我对话。',
          timestamp: Date.now(),
          message_id: generateMessageId()
        })
      }, 1000)
    } catch (error) {
      console.error('连接失败:', error)
      connectionStatus.value = 'disconnected'
      isConnected.value = false
    }
  }

  // 断开连接
  const disconnect = () => {
    isConnected.value = false
    connectionStatus.value = 'disconnected'
    console.log('WebSocket 连接已断开')
  }

  // 发送消息
  const sendMessage = async (message) => {
    if (!message.trim()) return

    // 添加用户消息
    const userMessage = {
      type: 'user',
      message: message.trim(),
      timestamp: Date.now(),
      message_id: generateMessageId()
    }
    addMessage(userMessage)

    try {
      // 调用后端API
      const response = await api.post('/api/chat', {
        message: message.trim(),
        session_id: currentSessionId.value || generateSessionId()
      })

      if (response.data && response.data.response) {
        // 添加AI回复
        const aiMessage = {
          type: 'chat_response',
          message: response.data.response,
          timestamp: Date.now(),
          message_id: generateMessageId(),
          analysis: response.data.analysis
        }
        addMessage(aiMessage)

        // 更新会话ID
        if (response.data.session_id) {
          currentSessionId.value = response.data.session_id
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      
      // 添加错误消息
      const errorMessage = {
        type: 'chat_response',
        message: '抱歉，我暂时无法回复您的消息。请稍后再试。',
        timestamp: Date.now(),
        message_id: generateMessageId()
      }
      addMessage(errorMessage)
      
      throw error
    }
  }

  // 添加消息
  const addMessage = (message) => {
    messages.value.push({
      ...message,
      timestamp: message.timestamp || Date.now(),
      message_id: message.message_id || generateMessageId()
    })
  }

  // 清空消息
  const clearMessages = () => {
    messages.value = []
    currentSessionId.value = null
    processingSteps.value = []
    currentProcessing.value = null
    analysisResult.value = null
    isProcessing.value = false
  }

  // 处理步骤管理
  const addProcessingStep = (step) => {
    processingSteps.value.push({
      ...step,
      id: step.id || Date.now(),
      timestamp: step.timestamp || new Date().toLocaleTimeString()
    })
    isProcessing.value = true
  }

  const updateProcessingStep = (step) => {
    const index = processingSteps.value.findIndex(s => s.id === step.id)
    if (index !== -1) {
      processingSteps.value[index] = { ...processingSteps.value[index], ...step }
    } else {
      addProcessingStep(step)
    }
  }

  const setCurrentProcessing = (message) => {
    currentProcessing.value = message
    isProcessing.value = !!message
  }

  // 分析结果管理
  const setAnalysisResult = (result) => {
    analysisResult.value = {
      ...result,
      timestamp: result.timestamp || Date.now()
    }
    isProcessing.value = false
  }

  const clearAnalysisResult = () => {
    analysisResult.value = null
  }

  // 工具函数
  const generateMessageId = () => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  const generateSessionId = () => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    currentSessionId.value = sessionId
    return sessionId
  }

  // 健康检查
  const checkHealth = async () => {
    try {
      const response = await api.get('/api/health')
      return response.data
    } catch (error) {
      console.error('健康检查失败:', error)
      return null
    }
  }

  // 获取会话列表
  const getSessions = async () => {
    try {
      const response = await api.get('/api/sessions')
      return response.data
    } catch (error) {
      console.error('获取会话列表失败:', error)
      return []
    }
  }

  return {
    // 状态
    isConnected,
    connectionStatus,
    messages,
    currentSessionId,
    isProcessing,
    processingSteps,
    currentProcessing,
    analysisResult,
    
    // 计算属性
    lastMessage,
    
    // 方法
    connect,
    disconnect,
    sendMessage,
    addMessage,
    clearMessages,
    addProcessingStep,
    updateProcessingStep,
    setCurrentProcessing,
    setAnalysisResult,
    clearAnalysisResult,
    checkHealth,
    getSessions,
    generateMessageId,
    generateSessionId
  }
}) 