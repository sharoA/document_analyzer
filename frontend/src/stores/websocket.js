import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import axios from 'axios'

export const useWebSocketStore = defineStore('websocket', () => {
  const ws = ref(null)
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const messages = ref([])
  const connectionStatus = ref('disconnected') // disconnected, connecting, connected, error
  
  // 添加模拟模式和API模式
  const mockMode = ref(false) // 改为false，使用真实API
  const apiMode = ref(true) // 使用HTTP API模式

  // API配置
  const apiConfig = {
    baseURL: 'http://localhost:8081', // 后端服务器地址
    timeout: 30000, // 30秒超时
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: false // 不发送cookies
  }

  // 创建axios实例
  const apiClient = axios.create(apiConfig)

  // 添加请求拦截器
  apiClient.interceptors.request.use(
    (config) => {
      console.log('发送API请求:', config)
      return config
    },
    (error) => {
      console.error('请求拦截器错误:', error)
      return Promise.reject(error)
    }
  )

  // 添加响应拦截器
  apiClient.interceptors.response.use(
    (response) => {
      console.log('API响应:', response)
      return response
    },
    (error) => {
      console.error('API响应错误:', error)
      if (error.code === 'ECONNREFUSED') {
        console.error('后端服务器连接被拒绝，请检查服务器是否运行')
      }
      return Promise.reject(error)
    }
  )

  const connect = () => {
    if (apiMode.value) {
      // 使用HTTP API模式
      isConnected.value = true
      isConnecting.value = false
      connectionStatus.value = 'connected'
      console.log('API模式已启用，连接到后端服务器')
      
      // 添加欢迎消息
      addMessage({
        type: 'system',
        message: '欢迎使用 analyDesign 智能需求分析系统！现在使用API模式与火山引擎交互。',
        timestamp: new Date().toISOString(),
        message_id: generateMessageId()
      })
      return
    }

    if (mockMode.value) {
      // 模拟连接成功
      setTimeout(() => {
        isConnected.value = true
        isConnecting.value = false
        connectionStatus.value = 'connected'
        console.log('模拟 WebSocket 连接已建立')
        
        // 添加欢迎消息
        addMessage({
          type: 'system',
          message: '欢迎使用 analyDesign 智能需求分析系统！',
          timestamp: new Date().toISOString(),
          message_id: generateMessageId()
        })
      }, 1000)
      return
    }

    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      return
    }

    isConnecting.value = true
    connectionStatus.value = 'connecting'

    try {
      // 根据当前协议选择 WebSocket 协议
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.hostname}:8765`
      
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        isConnected.value = true
        isConnecting.value = false
        connectionStatus.value = 'connected'
        console.log('WebSocket 连接已建立')
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (error) {
          console.error('解析消息失败:', error)
        }
      }

      ws.value.onclose = () => {
        isConnected.value = false
        isConnecting.value = false
        connectionStatus.value = 'disconnected'
        console.log('WebSocket 连接已关闭')
        
        // 自动重连
        setTimeout(() => {
          if (!isConnected.value) {
            connect()
          }
        }, 3000)
      }

      ws.value.onerror = (error) => {
        isConnecting.value = false
        connectionStatus.value = 'error'
        console.error('WebSocket 错误:', error)
      }

    } catch (error) {
      isConnecting.value = false
      connectionStatus.value = 'error'
      console.error('WebSocket 连接失败:', error)
    }
  }

  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  // 发送消息到后端API
  const sendMessageToAPI = async (message) => {
    try {
      console.log('发送消息到后端API:', message)
      
      // 添加用户消息到界面
      const userMessageId = generateMessageId()
      addMessage({
        type: 'user',
        message: message,
        timestamp: new Date().toISOString(),
        message_id: userMessageId
      })

      // 添加处理中消息
      const processingMessageId = generateMessageId()
      addMessage({
        type: 'processing',
        message: '正在分析您的需求，请稍候...',
        timestamp: new Date().toISOString(),
        message_id: processingMessageId
      })

      // 调用后端API
      const response = await apiClient.post('/api/chat', {
        message: message,
        session_id: generateSessionId(),
        timestamp: new Date().toISOString()
      })

      // 移除处理中消息
      messages.value = messages.value.filter(msg => msg.message_id !== processingMessageId)

      // 添加AI回复
      if (response.data && response.data.success) {
        addMessage({
          type: 'chat_response',
          message: response.data.response || response.data.message,
          timestamp: new Date().toISOString(),
          message_id: generateMessageId(),
          analysis: {
            confidence: response.data.confidence || 0.85,
            intent: response.data.intent,
            entities: response.data.entities
          }
        })
      } else {
        throw new Error(response.data?.error || '后端返回错误')
      }

      return userMessageId

    } catch (error) {
      console.error('API调用失败:', error)
      
      // 移除处理中消息
      messages.value = messages.value.filter(msg => msg.type !== 'processing')
      
      // 添加错误消息
      addMessage({
        type: 'error',
        message: `抱歉，服务暂时不可用：${error.message}。请检查后端服务是否正常运行。`,
        timestamp: new Date().toISOString(),
        message_id: generateMessageId()
      })

      return null
    }
  }

  const sendMessage = async (message) => {
    if (apiMode.value) {
      return await sendMessageToAPI(message)
    }

    if (mockMode.value) {
      // 模拟发送消息
      const messageData = {
        type: 'user',
        message: message,
        message_id: generateMessageId(),
        timestamp: new Date().toISOString()
      }
      
      // 添加用户消息
      addMessage(messageData)
      
      // 模拟AI回复
      setTimeout(() => {
        addMessage({
          type: 'chat_response',
          message: `感谢您的问题："${message}"。这是一个模拟回复，实际的AI分析功能需要连接到后端服务器。目前系统正在演示模式下运行。`,
          timestamp: new Date().toISOString(),
          message_id: generateMessageId(),
          analysis: {
            confidence: 0.85
          }
        })
      }, 1500)
      
      return messageData.message_id
    }

    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      const messageData = {
        type: 'chat',
        message: message,
        message_id: generateMessageId(),
        timestamp: new Date().toISOString()
      }
      
      ws.value.send(JSON.stringify(messageData))
      
      // 添加用户消息到消息列表
      addMessage({
        type: 'user',
        message: message,
        timestamp: new Date().toISOString(),
        message_id: messageData.message_id
      })
      
      return messageData.message_id
    } else {
      console.error('WebSocket 未连接')
      return null
    }
  }

  const handleMessage = (data) => {
    addMessage(data)
  }

  const addMessage = (message) => {
    messages.value.push(message)
  }

  const clearMessages = () => {
    messages.value = []
  }

  const generateMessageId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }

  const generateSessionId = () => {
    return 'session_' + Date.now().toString(36) + Math.random().toString(36).substr(2)
  }

  // 发送心跳
  const sendPing = () => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({
        type: 'ping',
        timestamp: new Date().toISOString()
      }))
    }
  }

  // 定期发送心跳
  setInterval(sendPing, 30000)

  return {
    ws,
    isConnected,
    isConnecting,
    connectionStatus,
    messages,
    mockMode,
    apiMode,
    connect,
    disconnect,
    sendMessage,
    addMessage,
    clearMessages
  }
}) 