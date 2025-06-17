import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8082',
  timeout: 120000,
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
    console.log('收到响应:', {
      status: response.status,
      url: response.config.url,
      method: response.config.method,
      dataType: typeof response.data,
      dataSize: JSON.stringify(response.data).length,
      data: response.data
    })
    return response
  },
  (error) => {
    console.error('响应错误详情:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method,
      data: error.response?.data,
      message: error.message,
      code: error.code
    })
    return Promise.reject(error)
  }
)

// 工具函数 - 移到前面定义
const generateClientId = () => {
  return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

const generateMessageId = () => {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

export const useWebSocketStore = defineStore('websocket', () => {
  // 状态
  const socket = ref(null)
  const isConnected = ref(false)
  const messages = ref([])
  const currentMessage = ref('')
  const isTyping = ref(false)
  const clientId = ref(generateClientId())
  const sessionId = ref(generateSessionId())
  
  // 文件解析相关状态
  const parsingTasks = ref(new Map())
  const currentParsingTask = ref(null)
  const parsingStatus = ref('idle') // idle, uploading, parsing, content_analyzing, ai_analyzing, completed, failed
  const parsingProgress = ref(0)
  const isProcessing = ref(false) // 新增：处理状态标志
  
  // 处理步骤
  const processingSteps = ref([])
  const currentProcessing = ref(null)
  const analysisResult = ref(null)
  
  // 节点进度状态
  const nodeProgress = ref({
    document_parsing: { progress: 0, message: '等待开始', status: 'pending', canStart: false },
    content_analysis: { progress: 0, message: '等待开始', status: 'pending', canStart: false },
    ai_analysis: { progress: 0, message: '等待开始', status: 'pending', canStart: false },
    document_generation: { progress: 0, message: '等待开始', status: 'pending', canStart: false }
  })
  
  // 添加轮询管理
  const activePolls = ref(new Map()) // 存储活跃的轮询定时器
  
  // 停止指定任务的轮询
  const stopPolling = (taskId, pollType = 'all') => {
    const pollKey = `${taskId}_${pollType}`
    if (activePolls.value.has(pollKey)) {
      clearTimeout(activePolls.value.get(pollKey))
      activePolls.value.delete(pollKey)
      console.log(`🛑 已停止轮询: ${pollKey}`)
    }
    
    // 如果是停止所有轮询
    if (pollType === 'all') {
      const keysToDelete = []
      activePolls.value.forEach((timerId, key) => {
        if (key.startsWith(taskId)) {
          clearTimeout(timerId)
          keysToDelete.push(key)
        }
      })
      keysToDelete.forEach(key => activePolls.value.delete(key))
      console.log(`🛑 已停止任务 ${taskId} 的所有轮询`)
    }
  }
  
  // 设置轮询定时器
  const setPollingTimer = (taskId, pollType, callback, delay = 2000) => {
    const pollKey = `${taskId}_${pollType}`
    
    // 先停止现有的轮询
    stopPolling(taskId, pollType)
    
    // 设置新的轮询
    const timerId = setTimeout(callback, delay)
    activePolls.value.set(pollKey, timerId)
    
    return timerId
  }

  // 计算属性
  const lastMessage = computed(() => {
    return messages.value.length > 0 ? messages.value[messages.value.length - 1] : null
  })

  const isFileProcessing = computed(() => {
    return parsingStatus.value === 'uploading' || 
           parsingStatus.value === 'parsing' || 
           parsingStatus.value === 'content_analyzing' || 
           parsingStatus.value === 'ai_analyzing'
  })

  // 连接方法（模拟模式）
  const connect = () => {
    try {
      isConnected.value = true
      console.log('WebSocket 连接成功（模拟模式）')
      
      // 添加欢迎消息
      addMessage({
        type: 'chat_response',
        message: '您好！我是智能需求分析助手，可以帮您分析需求文档。请上传您的文档开始分析，或者直接与我对话。',
        timestamp: Date.now(),
        message_id: generateMessageId()
      })
    } catch (error) {
      console.error('连接失败:', error)
      isConnected.value = false
    }
  }

  // 断开连接
  const disconnect = () => {
    isConnected.value = false
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
        session_id: sessionId.value
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

  // 文件上传和解析
  const uploadFile = async (file) => {
    try {
      parsingStatus.value = 'uploading'
      parsingProgress.value = 0
      
      // 检查文件大小（21MB限制）
      const maxFileSize = 21 * 1024 * 1024 // 21MB
      if (file.size > maxFileSize) {
        throw new Error(`文件大小 ${(file.size / (1024 * 1024)).toFixed(1)}MB 超过限制，最大允许 21MB`)
      }
      
      // 预先创建完整的处理流程节点
      const processingSteps = [
        {
          id: 'step_upload',
          title: '文档上传',
          description: '准备上传文档...',
          status: 'pending',
          progress: 0,
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: 'step_parsing',
          title: '文档解析',
          description: '等待文档上传完成...',
          status: 'pending',
          progress: 0,
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: 'step_content_analysis',
          title: '内容分析',
          description: '等待文档解析完成...',
          status: 'pending',
          progress: 0,
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: 'step_ai_analysis',
          title: '智能解析',
          description: '等待内容分析完成...',
          status: 'pending',
          progress: 0,
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: 'step_markdown',
          title: '生成报告',
          description: '等待智能解析完成...',
          status: 'pending',
          progress: 0,
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: 'step_complete',
          title: '完成处理',
          description: '等待报告生成完成...',
          status: 'pending',
          progress: 0,
          timestamp: new Date().toLocaleTimeString()
        }
      ]
      
      // 清空之前的处理步骤并添加新的步骤
      clearProcessingSteps()
      processingSteps.forEach(step => addProcessingStep(step))
      
      // 开始第一步：文档上传
      updateProcessingStep({
        id: 'step_upload',
        title: '文档上传',
        description: '正在上传文档...',
        status: 'primary',
        progress: 10,
        timestamp: new Date().toLocaleTimeString()
      })
      
      // 将文件转换为base64
      const fileContent = await fileToBase64(file.raw)
      
      const fileInfo = {
        name: file.name,
        type: file.raw.type,
        size: file.size,
        content: fileContent
      }

      // 调用后端文件上传API
      const response = await api.post('/api/file/upload', {
        file_info: fileInfo,
        client_id: clientId.value
      })

      if (response.data.success) {
        const taskId = response.data.task_id
        
        // 文档上传完成
        updateProcessingStep({
          id: 'step_upload',
          title: '文档上传',
          description: '文档上传成功',
          status: 'success',
          progress: 100,
          timestamp: new Date().toLocaleTimeString()
        })
        
        // 创建解析任务记录
        const task = {
          id: taskId,
          fileName: file.name,
          fileType: file.raw.type,
          fileSize: file.size,
          filePath: response.data.file_path,
          status: 'pending',
          progress: 0,
          steps: [],
          result: null,
          contentAnalysis: null,
          aiAnalysis: null,
          error: null,
          createdAt: new Date(),
          updatedAt: new Date()
        }
        
        parsingTasks.value.set(taskId, task)
        currentParsingTask.value = task
        parsingStatus.value = 'parsing'
        
        // 开始第二步：文档解析
        updateProcessingStep({
          id: 'step_parsing',
          title: '文档解析',
          description: '正在解析文档内容...',
          status: 'primary',
          progress: 10,
          timestamp: new Date().toLocaleTimeString()
        })
        
        // 开始轮询解析状态
        pollParsingStatus(taskId)
        
        return { success: true, taskId }
      } else {
        throw new Error(response.data.error || '文件上传失败')
      }
    } catch (error) {
      console.error('文件上传失败:', error)
      parsingStatus.value = 'failed'
      
      // 更新上传步骤为失败状态
      updateProcessingStep({
        id: 'step_upload',
        title: '文档上传',
        description: `上传失败: ${error.message}`,
        status: 'error',
        progress: 0,
        timestamp: new Date().toLocaleTimeString()
      })
      
      throw error
    }
  }

  // 轮询解析状态 - 修改为严格顺序控制
  const pollParsingStatus = async (taskId) => {
    const maxAttempts = 60 // 最多轮询60次（约2分钟）
    let attempts = 0
    
    const poll = async () => {
      try {
        attempts++
        console.log(`📄 文档解析轮询 - 第${attempts}次，任务ID: ${taskId}`)
        
        // 检查全局状态
        if (parsingStatus.value === 'completed' || parsingStatus.value === 'failed') {
          console.log('🛑 全局状态已完成/失败，停止解析轮询')
          stopPolling(taskId, 'parsing')
          return
        }
        
        const response = await api.get(`/api/file/parsing/${taskId}`)
        
        if (response.data.success) {
          const task = response.data
          console.log(`📄 文档解析状态: ${task.status}, 进度: ${task.progress}%`)
          
          // 更新任务状态
          const localTask = parsingTasks.value.get(taskId)
          if (localTask) {
            Object.assign(localTask, {
              status: task.status,
              progress: task.progress,
              steps: task.steps || [],
              result: task.result,
              error: task.error,
              updatedAt: new Date()
            })
            
            parsingProgress.value = task.progress
            
            // 重要：更新当前解析任务的步骤信息
            if (currentParsingTask.value && currentParsingTask.value.id === taskId) {
              currentParsingTask.value.status = task.status
              currentParsingTask.value.progress = task.progress
              currentParsingTask.value.steps = task.steps || []
              currentParsingTask.value.result = task.result
              currentParsingTask.value.error = task.error
              currentParsingTask.value.updatedAt = new Date()
            }
            
            // 更新文档解析步骤
            updateProcessingStep({
              id: 'step_parsing',
              title: '文档解析',
              description: task.current_step || '正在解析文档内容...',
              status: 'primary',
              progress: task.progress,
              timestamp: new Date().toLocaleTimeString()
            })
          }
          
          // 严格检查：只有当状态为 'parsed' 且进度为 100% 时才进入下一步
          if (task.status === 'parsed' && task.progress === 100) {
            console.log('✅ 文档解析完成，准备进入内容分析阶段')
            // 文档解析完成
            stopPolling(taskId, 'parsing') // 停止解析轮询
            updateProcessingStep({
              id: 'step_parsing',
              title: '文档解析',
              description: '文档解析完成',
              status: 'success',
              progress: 100,
              timestamp: new Date().toLocaleTimeString()
            })
            
            // 等待1秒后开始内容分析，确保状态稳定
            setTimeout(() => {
              // 开始第三步：内容分析
              updateProcessingStep({
                id: 'step_content_analysis',
                title: '内容分析',
                description: '正在启动内容分析...',
                status: 'primary',
                progress: 0,
                timestamp: new Date().toLocaleTimeString()
              })
              
              parsingStatus.value = 'content_analyzing'
              startContentAnalysis(taskId)
            }, 1000)
            return
          } else if (task.status === 'failed') {
            console.log('❌ 文档解析失败')
            parsingStatus.value = 'failed'
            stopPolling(taskId, 'all') // 停止所有轮询
            
            // 更新解析步骤为失败状态
            updateProcessingStep({
              id: 'step_parsing',
              title: '文档解析',
              description: `解析失败: ${task.error || '未知错误'}`,
              status: 'error',
              progress: 0,
              timestamp: new Date().toLocaleTimeString()
            })
            
            // 添加失败消息
            addMessage({
              type: 'chat_response',
              message: `文件解析失败：${task.error || '未知错误'}`,
              timestamp: Date.now(),
              message_id: generateMessageId()
            })
            
            return
          }
          
          // 继续轮询 - 只有在处理中的状态才继续
          if (attempts < maxAttempts && (task.status === 'pending' || task.status === 'processing' || task.status === 'parsing')) {
            console.log(`⏳ 文档解析进行中，${2.5}秒后继续轮询...`)
            setPollingTimer(taskId, 'parsing', poll, 2500) // 增加到2.5秒
          } else if (attempts >= maxAttempts) {
            console.log('⏰ 文档解析轮询超时')
            parsingStatus.value = 'failed'
            stopPolling(taskId, 'all')
            
            updateProcessingStep({
              id: 'step_parsing',
              title: '文档解析',
              description: '解析超时，请重试',
              status: 'error',
              progress: 0,
              timestamp: new Date().toLocaleTimeString()
            })
            
            addMessage({
              type: 'chat_response',
              message: '文件解析超时，请重试。',
              timestamp: Date.now(),
              message_id: generateMessageId()
            })
          }
        }
      } catch (error) {
        console.error('轮询解析状态失败:', error)
        
        // 检查是否是404错误（任务不存在）
        if (error.response && error.response.status === 404) {
          console.log('❌ 解析任务不存在，停止轮询')
          parsingStatus.value = 'failed'
          stopPolling(taskId, 'all')
          
          updateProcessingStep({
            id: 'step_parsing',
            title: '文档解析',
            description: '任务已丢失，请重新上传文件',
            status: 'error',
            progress: 0,
            timestamp: new Date().toLocaleTimeString()
          })
          
          addMessage({
            type: 'chat_response',
            message: '解析任务已丢失，可能是服务器重启导致。请重新上传文件。',
            timestamp: Date.now(),
            message_id: generateMessageId()
          })
          
          // 清理当前任务
          if (currentParsingTask.value && currentParsingTask.value.id === taskId) {
            currentParsingTask.value = null
          }
          parsingTasks.value.delete(taskId)
          
          return // 停止轮询
        }
        
        // 其他错误，继续重试
        if (attempts >= maxAttempts) {
          parsingStatus.value = 'failed'
          stopPolling(taskId, 'all')
          updateProcessingStep({
            id: 'step_parsing',
            title: '文档解析',
            description: '解析失败，请重试',
            status: 'error',
            progress: 0,
            timestamp: new Date().toLocaleTimeString()
          })
        } else {
          console.log(`🔄 解析轮询遇到错误，${2.5}秒后重试...`)
          setPollingTimer(taskId, 'parsing', poll, 2500) // 增加到2.5秒
        }
      }
    }
    
    poll()
  }

  // 开始内容分析
  const startContentAnalysis = async (taskId) => {
    try {
      // 设置状态为内容分析中
      parsingStatus.value = 'content_analyzing'
      
      updateProcessingStep({
        id: 'step_content_analysis',
        title: '内容分析',
        description: '正在分析文档内容结构和关键信息...',
        status: 'primary',
        progress: 30,
        timestamp: new Date().toLocaleTimeString()
      })

      const response = await api.post(`/api/file/analyze/${taskId}`, {})
      
      if (response.data.success) {
        // 开始轮询内容分析状态
        pollContentAnalysisStatus(taskId)
      } else {
        throw new Error(response.data.error || '启动内容分析失败')
      }
    } catch (error) {
      console.error('启动内容分析失败:', error)
      parsingStatus.value = 'failed'
      
      updateProcessingStep({
        id: 'step_content_analysis',
        title: '内容分析',
        description: `内容分析启动失败: ${error.message}`,
        status: 'error',
        progress: 0,
        timestamp: new Date().toLocaleTimeString()
      })
      
      addMessage({
        type: 'chat_response',
        message: `内容分析启动失败：${error.message}`,
        timestamp: Date.now(),
        message_id: generateMessageId()
      })
    }
  }

  // 轮询内容分析状态 - 修改为严格顺序控制
  const pollContentAnalysisStatus = async (taskId) => {
    const maxAttempts = 30
    let attempts = 0
    
    const poll = async () => {
      try {
        attempts++
        console.log(`🔍 内容分析轮询 - 第${attempts}次，任务ID: ${taskId}`)
        
        // 检查全局状态
        if (parsingStatus.value === 'completed' || parsingStatus.value === 'failed') {
          console.log('🛑 全局状态已完成/失败，停止内容分析轮询')
          stopPolling(taskId, 'content_analysis')
          return
        }
        
        const response = await api.get(`/api/file/parsing/${taskId}`)
        
        if (response.data.success) {
          const task = response.data
          console.log(`🔍 内容分析状态: ${task.status}, 进度: ${task.progress}%`)
          
          const localTask = parsingTasks.value.get(taskId)
          
          if (localTask) {
            localTask.status = task.status
            localTask.progress = task.progress
            localTask.steps = task.steps || []
            localTask.updatedAt = new Date()
          }
          
          // 重要：更新当前解析任务的步骤信息
          if (currentParsingTask.value && currentParsingTask.value.id === taskId) {
            currentParsingTask.value.status = task.status
            currentParsingTask.value.progress = task.progress
            currentParsingTask.value.steps = task.steps || []
            currentParsingTask.value.updatedAt = new Date()
          }
          
          // 更新内容分析步骤
          if (task.status === 'content_analyzing') {
            updateProcessingStep({
              id: 'step_content_analysis',
              title: '内容分析',
              description: task.current_step || '正在分析文档内容...',
              status: 'primary',
              progress: Math.min(task.progress, 90), // 最多到90%，完成时才100%
              timestamp: new Date().toLocaleTimeString()
            })
          }
          
          // 严格检查：只有当状态为 'content_analyzed' 且进度为 100% 时才进入下一步
          if (task.status === 'content_analyzed' && task.progress === 100) {
            console.log('✅ 内容分析完成，准备进入AI智能解析阶段')
            // 内容分析完成
            stopPolling(taskId, 'content_analysis') // 停止内容分析轮询
            updateProcessingStep({
              id: 'step_content_analysis',
              title: '内容分析',
              description: '内容分析完成',
              status: 'success',
              progress: 100,
              timestamp: new Date().toLocaleTimeString()
            })
            
            // 等待1秒后开始AI分析，确保状态稳定
            setTimeout(() => {
              // 开始第四步：智能解析
              updateProcessingStep({
                id: 'step_ai_analysis',
                title: '智能解析',
                description: '正在启动AI智能解析...',
                status: 'primary',
                progress: 0,
                timestamp: new Date().toLocaleTimeString()
              })
              
              parsingStatus.value = 'ai_analyzing'
              startAIAnalysis(taskId)
            }, 1000)
            return
          } else if (task.status === 'content_failed') {
            console.log('❌ 内容分析失败')
            parsingStatus.value = 'failed'
            stopPolling(taskId, 'all')
            
            updateProcessingStep({
              id: 'step_content_analysis',
              title: '内容分析',
              description: `内容分析失败: ${task.error || '未知错误'}`,
              status: 'error',
              progress: 0,
              timestamp: new Date().toLocaleTimeString()
            })
            
            addMessage({
              type: 'chat_response',
              message: `内容分析失败：${task.error || '未知错误'}`,
              timestamp: Date.now(),
              message_id: generateMessageId()
            })
            
            return
          }
          
          // 继续轮询 - 只有在分析中的状态才继续
          if (attempts < maxAttempts && task.status === 'content_analyzing') {
            console.log(`⏳ 内容分析进行中，${2.5}秒后继续轮询...`)
            setPollingTimer(taskId, 'content_analysis', poll, 2500) // 增加到2.5秒
          } else if (attempts >= maxAttempts) {
            console.log('⏰ 内容分析轮询超时')
            parsingStatus.value = 'failed'
            stopPolling(taskId, 'all')
            
            updateProcessingStep({
              id: 'step_content_analysis',
              title: '内容分析',
              description: '内容分析超时，请重试',
              status: 'error',
              progress: 0,
              timestamp: new Date().toLocaleTimeString()
            })
            
            addMessage({
              type: 'chat_response',
              message: '内容分析超时，请重试。',
              timestamp: Date.now(),
              message_id: generateMessageId()
            })
          }
        }
      } catch (error) {
        console.error('轮询内容分析状态失败:', error)
        
        // 检查是否是404错误（任务不存在）
        if (error.response && error.response.status === 404) {
          console.log('❌ 内容分析任务不存在，停止轮询')
          parsingStatus.value = 'failed'
          stopPolling(taskId, 'all')
          
          updateProcessingStep({
            id: 'step_content_analysis',
            title: '内容分析',
            description: '任务已丢失，请重新上传文件',
            status: 'error',
            progress: 0,
            timestamp: new Date().toLocaleTimeString()
          })
          
          addMessage({
            type: 'chat_response',
            message: '内容分析任务已丢失，可能是服务器重启导致。请重新上传文件。',
            timestamp: Date.now(),
            message_id: generateMessageId()
          })
          
          // 清理当前任务
          if (currentParsingTask.value && currentParsingTask.value.id === taskId) {
            currentParsingTask.value = null
          }
          parsingTasks.value.delete(taskId)
          
          return // 停止轮询
        }
        
        // 其他错误，继续重试
        if (attempts >= maxAttempts) {
          parsingStatus.value = 'failed'
          stopPolling(taskId, 'all')
          updateProcessingStep({
            id: 'step_content_analysis',
            title: '内容分析',
            description: '内容分析失败，请重试',
            status: 'error',
            progress: 0,
            timestamp: new Date().toLocaleTimeString()
          })
        } else {
          console.log(`🔄 内容分析轮询遇到错误，${2.5}秒后重试...`)
          setPollingTimer(taskId, 'content_analysis', poll, 2500) // 增加到2.5秒
        }
      }
    }
    
    poll()
  }

  // 开始AI分析
  const startAIAnalysis = async (taskId, analysisType = 'comprehensive', customPrompt = '') => {
    try {
      // 设置状态为AI分析中
      parsingStatus.value = 'ai_analyzing'
      
      updateProcessingStep({
        id: 'step_ai_analysis',
        title: '智能解析',
        description: '正在使用AI进行深度文档分析...',
        status: 'primary',
        progress: 30,
        timestamp: new Date().toLocaleTimeString()
      })

      const response = await api.post(`/api/file/ai-analyze/${taskId}`, {
        analysis_type: analysisType,
        custom_prompt: customPrompt
      })
      
      if (response.data.success) {
        // 开始轮询AI分析状态
        pollAIAnalysisStatus(taskId)
      } else {
        throw new Error(response.data.error || '启动智能解析失败')
      }
    } catch (error) {
      console.error('启动智能解析失败:', error)
      parsingStatus.value = 'failed'
      
      updateProcessingStep({
        id: 'step_ai_analysis',
        title: '智能解析',
        description: `智能解析启动失败: ${error.message}`,
        status: 'error',
        progress: 0,
        timestamp: new Date().toLocaleTimeString()
      })
      
      addMessage({
        type: 'chat_response',
        message: `智能解析启动失败：${error.message}`,
        timestamp: Date.now(),
        message_id: generateMessageId()
      })
    }
  }

  // 轮询AI分析状态 - 修改为严格顺序控制并生成Markdown
  const pollAIAnalysisStatus = async (taskId) => {
    const maxAttempts = 60 // AI分析可能需要更长时间
    let attempts = 0
    
    const poll = async () => {
      try {
        attempts++
        console.log(`🤖 AI分析轮询 - 第${attempts}次，任务ID: ${taskId}`)
        
        // 检查全局状态，如果已经完成则停止轮询
        if (parsingStatus.value === 'completed') {
          console.log('🛑 全局状态已完成，停止AI分析轮询')
          stopPolling(taskId, 'ai_analysis')
          return
        }
        
        const response = await api.get(`/api/file/result/${taskId}`)
        
        if (response.data.success) {
          const task = response.data
          console.log(`🤖 AI分析状态: ${task.current_step || task.status}, 进度: ${task.overall_progress || task.progress || 0}%`)
          
          const localTask = parsingTasks.value.get(taskId)
          
          if (localTask) {
            localTask.status = task.current_step || task.status
            localTask.result = task.interfaces?.document_parsing?.data || task.parsing_result
            localTask.contentAnalysis = task.interfaces?.content_analysis?.data || task.content_analysis
            localTask.aiAnalysis = task.interfaces?.ai_analysis?.data || task.ai_analysis
            localTask.updatedAt = new Date()
          }
          
          // 更新AI分析步骤进度
          if (task.status === 'ai_analyzing') {
            console.log('🤖 AI分析进行中，继续轮询...')
            updateProcessingStep({
              id: 'step_ai_analysis',
              title: '智能解析',
              description: '正在进行AI智能分析...',
              status: 'primary',
              progress: Math.min(70, 70 + (attempts * 2)), // 逐步增加进度
              timestamp: new Date().toLocaleTimeString()
            })
            
            // 继续轮询 - 使用轮询管理，增加间隔到3秒
            if (attempts < maxAttempts) {
              console.log(`⏳ AI分析进行中，${3}秒后继续轮询...`)
              setPollingTimer(taskId, 'ai_analysis', poll, 3000) // 增加到3秒
            } else {
              // 超时处理
              console.log('⏰ AI分析轮询超时')
              parsingStatus.value = 'failed'
              stopPolling(taskId, 'all') // 停止所有轮询
              updateProcessingStep({
                id: 'step_ai_analysis',
                title: '智能解析',
                description: '智能解析超时，请重试',
                status: 'error',
                progress: 0,
                timestamp: new Date().toLocaleTimeString()
              })
              addMessage({
                type: 'chat_response',
                message: '智能解析超时，请重试。',
                timestamp: Date.now(),
                message_id: generateMessageId()
              })
            }
            return
          }
          
          // 严格检查：当AI分析完成时就停止轮询
          if (task.current_step === 'ai_analyzed' || task.status === 'fully_completed' || 
              (task.interfaces && task.interfaces.ai_analysis && task.interfaces.ai_analysis.status === 'completed')) {
            console.log('🎉 AI分析完成，开始生成Markdown文档！')
            // AI分析完成 - 立即停止所有轮询
            stopPolling(taskId, 'all') // 停止该任务的所有轮询
            
            // AI分析完成
            updateProcessingStep({
              id: 'step_ai_analysis',
              title: '智能解析',
              description: '智能解析完成',
              status: 'success',
              progress: 100,
              timestamp: new Date().toLocaleTimeString()
            })
            
            // 第五步：生成Markdown文档
            updateProcessingStep({
              id: 'step_markdown',
              title: '生成报告',
              description: '正在生成Markdown分析报告...',
              status: 'primary',
              progress: 50,
              timestamp: new Date().toLocaleTimeString()
            })
            
            // 生成Markdown文档
            const markdownContent = generateMarkdownReport(task)
            
            // 完成Markdown生成
            updateProcessingStep({
              id: 'step_markdown',
              title: '生成报告',
              description: 'Markdown分析报告生成完成',
              status: 'success',
              progress: 100,
              timestamp: new Date().toLocaleTimeString()
            })
            
            // 第六步：完成处理
            updateProcessingStep({
              id: 'step_complete',
              title: '完成处理',
              description: '所有分析步骤已完成！',
              status: 'success',
              progress: 100,
              timestamp: new Date().toLocaleTimeString()
            })
            
            // 更新解析进度和状态
            parsingProgress.value = 100
            parsingStatus.value = 'completed'
            console.log(`✅ 全局状态已更新: parsingStatus = ${parsingStatus.value}`)
            
            // 更新当前解析任务的状态和步骤
            if (currentParsingTask.value && currentParsingTask.value.id === taskId) {
              currentParsingTask.value.status = 'fully_completed'
              currentParsingTask.value.progress = 100
              currentParsingTask.value.result = task.interfaces?.document_parsing?.data || task.parsing_result
              currentParsingTask.value.contentAnalysis = task.interfaces?.content_analysis?.data || task.content_analysis
              currentParsingTask.value.aiAnalysis = task.interfaces?.ai_analysis?.data || task.ai_analysis
              currentParsingTask.value.markdownContent = markdownContent // 添加Markdown内容
              currentParsingTask.value.updatedAt = new Date()
              
              // 添加最终完成步骤到解析任务的步骤列表
              if (!currentParsingTask.value.steps) {
                currentParsingTask.value.steps = []
              }
              
              // 检查是否已经有完成步骤，避免重复添加 - 添加安全检查
              const hasCompletedStep = currentParsingTask.value.steps.some(step => 
                step && (step.status === 'fully_completed' || (step.step && step.step.includes('全部完成')))
              )
              
              if (!hasCompletedStep) {
                currentParsingTask.value.steps.push({
                  step: '文档分析全部完成',
                  progress: 100,
                  timestamp: new Date().toLocaleTimeString(),
                  status: 'fully_completed'
                })
              }
            }
            
            // 设置完整的分析结果，包含Markdown内容
            const parsingData = task.interfaces?.document_parsing?.data || task.parsing_result
            if (parsingData || task.file_info) {
              setAnalysisResult({
                title: `📄 ${task.file_info?.name || parsingData?.file_name || '未知文件'} - 分析报告`,
                type: 'comprehensive',
                timestamp: Date.now(),
                fileInfo: {
                  name: task.file_info?.name || parsingData?.file_name || '未知文件',
                  type: task.file_info?.type || parsingData?.file_type || 'unknown',
                  size: task.file_info?.size || parsingData?.file_size || 0
                },
                content: parsingData?.text_content || parsingData?.content || '',
                details: parsingData,
                contentAnalysis: task.interfaces?.content_analysis?.data || task.content_analysis,
                aiAnalysis: task.interfaces?.ai_analysis?.data || task.ai_analysis,
                markdownContent: markdownContent // 添加Markdown内容
              })
            }
            
            // 添加完成消息
            addMessage({
              type: 'chat_response',
              message: `文档 "${task.file_info?.name || '未知文件'}" 的完整分析已完成！已生成Markdown分析报告。您可以在"解析结果"页签中查看详细内容。`,
              timestamp: Date.now(),
              message_id: generateMessageId()
            })
            
            // 立即返回，停止轮询
            console.log('🛑 AI分析轮询已完全停止')
            return
          }
          
          if (task.current_step === 'ai_failed' || task.status === 'ai_failed') {
            console.log('❌ AI分析失败，停止轮询')
            parsingStatus.value = 'failed'
            stopPolling(taskId, 'all') // 停止所有轮询
            
            updateProcessingStep({
              id: 'step_ai_analysis',
              title: '智能解析',
              description: `智能解析失败: ${task.error || '未知错误'}`,
              status: 'error',
              progress: 0,
              timestamp: new Date().toLocaleTimeString()
            })
            
            addMessage({
              type: 'chat_response',
              message: `智能解析失败：${task.error || '未知错误'}`,
              timestamp: Date.now(),
              message_id: generateMessageId()
            })
            
            return
          }
          
          // 如果状态不是预期的，记录并继续轮询
          console.log(`⚠️ 未知状态: ${task.status}，继续轮询...`)
          if (attempts < maxAttempts) {
            console.log(`🔄 AI分析状态检查，${3}秒后继续轮询...`)
            setPollingTimer(taskId, 'ai_analysis', poll, 3000) // 增加到3秒
          }
        }
      } catch (error) {
        console.error('轮询智能解析状态失败:', error)
        
        // 检查是否是404错误（任务不存在）
        if (error.response && error.response.status === 404) {
          console.log('❌ 任务不存在，停止轮询')
          parsingStatus.value = 'failed'
          stopPolling(taskId, 'all') // 停止所有轮询
          
          updateProcessingStep({
            id: 'step_ai_analysis',
            title: '智能解析',
            description: '任务已丢失，请重新上传文件',
            status: 'error',
            progress: 0,
            timestamp: new Date().toLocaleTimeString()
          })
          
          addMessage({
            type: 'chat_response',
            message: '任务已丢失，可能是服务器重启导致。请重新上传文件进行分析。',
            timestamp: Date.now(),
            message_id: generateMessageId()
          })
          
          // 清理当前任务
          if (currentParsingTask.value && currentParsingTask.value.id === taskId) {
            currentParsingTask.value = null
          }
          parsingTasks.value.delete(taskId)
          
          return // 停止轮询
        }
        
        // 其他错误，继续重试
        if (attempts >= maxAttempts) {
          parsingStatus.value = 'failed'
          stopPolling(taskId, 'all') // 停止所有轮询
          updateProcessingStep({
            id: 'step_ai_analysis',
            title: '智能解析',
            description: '智能解析失败，请重试',
            status: 'error',
            progress: 0,
            timestamp: new Date().toLocaleTimeString()
          })
        } else {
          console.log(`🔄 AI分析轮询遇到错误，${3}秒后重试...`)
          setPollingTimer(taskId, 'ai_analysis', poll, 3000) // 增加到3秒
        }
      }
    }
    
    // 开始轮询
    poll()
  }

  // 获取解析状态
  const getParsingStatus = async (taskId) => {
    try {
      const response = await api.get(`/api/file/parsing/${taskId}`)
      return response.data
    } catch (error) {
      console.error('获取解析状态失败:', error)
      return null
    }
  }

  // 文件转base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => {
        // 移除data:xxx;base64,前缀
        const base64 = reader.result.split(',')[1]
        resolve(base64)
      }
      reader.onerror = error => reject(error)
    })
  }

  // 重置文件解析状态
  const resetParsingState = () => {
    // 停止所有活跃的轮询
    activePolls.value.forEach((timerId, key) => {
      clearTimeout(timerId)
      console.log(`🛑 清理轮询: ${key}`)
    })
    activePolls.value.clear()
    
    parsingStatus.value = 'idle'
    parsingProgress.value = 0
    currentParsingTask.value = null
    parsingTasks.value.clear()
    console.log('✅ 解析状态已重置，所有轮询已停止')
  }

  // 清理所有轮询（用于页面卸载或重置）
  const clearAllPolling = () => {
    activePolls.value.forEach((timerId, key) => {
      clearTimeout(timerId)
      console.log(`🛑 强制清理轮询: ${key}`)
    })
    activePolls.value.clear()
    console.log('✅ 所有轮询已强制清理')
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
    sessionId.value = generateSessionId()
    processingSteps.value = []
    currentProcessing.value = null
    analysisResult.value = null
    isTyping.value = false
    resetParsingState()
  }

  // 处理步骤管理
  const addProcessingStep = (step) => {
    processingSteps.value.push({
      ...step,
      id: step.id || Date.now(),
      timestamp: step.timestamp || new Date().toLocaleTimeString()
    })
  }

  const updateProcessingStep = (step) => {
    const index = processingSteps.value.findIndex(s => s.id === step.id)
    if (index !== -1) {
      processingSteps.value[index] = { ...processingSteps.value[index], ...step }
    } else {
      addProcessingStep(step)
    }
  }

  const clearProcessingSteps = () => {
    processingSteps.value = []
    currentProcessing.value = null
  }

  const setCurrentProcessing = (message) => {
    currentProcessing.value = message
  }

  // 分析结果管理
  const setAnalysisResult = (result) => {
    analysisResult.value = {
      ...result,
      timestamp: result.timestamp || Date.now()
    }
  }

  const clearAnalysisResult = () => {
    analysisResult.value = null
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

  // 获取已上传文件列表
  const getUploadedFiles = async () => {
    try {
      const response = await api.get('/api/file/list')
      return response.data
    } catch (error) {
      console.error('获取文件列表失败:', error)
      return { success: false, files: [], error: error.message }
    }
  }

  // 删除已上传文件
  const deleteUploadedFile = async (taskId) => {
    try {
      const response = await api.delete(`/api/file/delete/${taskId}`)
      return response.data
    } catch (error) {
      console.error('删除文件失败:', error)
      return { success: false, error: error.message }
    }
  }

  // 重新定义generateSessionId为内部函数
  const updateSessionId = () => {
    const newSessionId = generateSessionId()
    sessionId.value = newSessionId
    return newSessionId
  }

  // 生成Markdown分析报告
  const generateMarkdownReport = (task) => {
    const currentTime = new Date().toLocaleString('zh-CN')
    const fileInfo = task.file_info || {}
    
    // 新的数据结构 - 三接口整合结果
    const interfaces = task.interfaces || {}
    const documentParsing = interfaces.document_parsing || {}
    const contentAnalysis = interfaces.content_analysis || {}
    const aiAnalysis = interfaces.ai_analysis || {}
    
    // 提取各接口的数据
    const parsingData = documentParsing.data || {}
    const contentData = contentAnalysis.data || {}
    const aiData = aiAnalysis.data || {}
    
    // 提取CRUD分析和业务洞察
    const crudAnalysis = contentData.crud_analysis || {}
    const businessInsights = contentData.business_insights || {}
    
    // 提取AI分析的接口设计和MQ配置
    const apiInterfaces = aiData.api_interfaces || []
    const mqConfiguration = aiData.mq_configuration || {}
    const technicalSpecs = aiData.technical_specifications || {}
    
    let markdown = `# 文档分析报告

## 📋 基本信息

| 项目 | 内容 |
|------|------|
| 文件名称 | ${fileInfo.name || '未知文件'} |
| 文件类型 | ${fileInfo.type || '未知类型'} |
| 文件大小 | ${fileInfo.size ? (fileInfo.size / 1024).toFixed(2) + ' KB' : '未知大小'} |
| 分析时间 | ${currentTime} |
| 任务ID | ${task.task_id || 'N/A'} |
| 整体状态 | ${task.overall_status || '未知'} |
| 整体进度 | ${task.overall_progress || 0}% |

---

## 📄 文档解析结果

### 接口状态
- **接口名称**: ${documentParsing.interface_name || '文档解析接口'}
- **接口地址**: ${documentParsing.endpoint || 'N/A'}
- **处理状态**: ${documentParsing.status === 'completed' ? '✅ 已完成' : '⏳ 处理中'}

### 文档类型
${parsingData.file_type || '未识别'}

### 文档内容统计
- **字符数**: ${parsingData.char_count || 0}
- **行数**: ${parsingData.line_count || 'N/A'}
- **文件大小**: ${parsingData.file_size ? (parsingData.file_size / 1024).toFixed(2) + ' KB' : '未知'}
- **解析方法**: ${parsingData.analysis_method || '标准解析'}

### 文档特征
- **语言**: ${contentData.language || '未识别'}
- **文档类型**: ${contentData.document_type || '未分类'}
- **复杂度等级**: ${contentData.complexity_level || '中等'}
- **词汇数量**: ${contentData.word_count || 0}
- **字符数量**: ${contentData.char_count || 0}

### 结构分析
${contentData.structure_analysis ? `
- **段落数**: ${contentData.structure_analysis.paragraphs || 0}
- **行数**: ${contentData.structure_analysis.lines || 0}
- **章节数**: ${contentData.structure_analysis.sections || 0}
` : '无结构分析数据'}

### 内容摘要
${contentData.summary || parsingData.summary || '无摘要信息'}

### 关键词
${contentData.keywords && contentData.keywords.length > 0 ? 
  contentData.keywords.map(keyword => `- ${keyword}`).join('\n') : 
  '无关键词信息'}

---

## 🔍 内容分析结果

### 接口状态
- **接口名称**: ${contentAnalysis.interface_name || '内容分析接口'}
- **接口地址**: ${contentAnalysis.endpoint || 'N/A'}
- **处理状态**: ${contentAnalysis.status === 'completed' ? '✅ 已完成' : '⏳ 处理中'}

### CRUD操作分析
${crudAnalysis.operations && crudAnalysis.operations.length > 0 ? `
#### 识别的操作类型
${crudAnalysis.operations.map(op => `
- **${op.type}**: ${op.description}
  - 关键词: ${op.keywords_found ? op.keywords_found.join(', ') : '无'}
  - 复杂度: ${op.estimated_complexity || '未知'}
`).join('')}

#### 操作统计
- **总操作数**: ${crudAnalysis.total_operations || 0}
- **操作类型**: ${crudAnalysis.operation_types ? crudAnalysis.operation_types.join(', ') : '无'}
` : '暂未识别到明确的CRUD操作'}

### 业务需求分析
${crudAnalysis.requirements && crudAnalysis.requirements.length > 0 ? 
  crudAnalysis.requirements.map(req => `- ${req}`).join('\n') : 
  '- 暂无明确的业务需求'}

### 功能变更分析
${crudAnalysis.changes && crudAnalysis.changes.length > 0 ? 
  crudAnalysis.changes.map(change => `- ${change}`).join('\n') : 
  '- 暂无功能变更信息'}

### 业务洞察
${businessInsights.main_functions && businessInsights.main_functions.length > 0 ? `
#### 主要功能
${businessInsights.main_functions.map(func => `- ${func}`).join('\n')}

#### 技术要求
${businessInsights.technical_requirements && businessInsights.technical_requirements.length > 0 ? 
  businessInsights.technical_requirements.map(req => `- ${req}`).join('\n') : 
  '- 暂无特殊技术要求'}

#### 优先级功能
${businessInsights.priority_features && businessInsights.priority_features.length > 0 ? 
  businessInsights.priority_features.map(feature => `- ${feature}`).join('\n') : 
  '- 暂无优先级排序'}

#### 预估开发时间
${businessInsights.estimated_development_time || '未评估'}
` : '暂无业务洞察信息'}

---

## 🤖 AI智能分析

### 接口状态
- **接口名称**: ${aiAnalysis.interface_name || 'AI智能分析接口'}
- **接口地址**: ${aiAnalysis.endpoint || 'N/A'}
- **处理状态**: ${aiAnalysis.status === 'completed' ? '✅ 已完成' : '⏳ 处理中'}

### 具体开发接口设计
${apiInterfaces && apiInterfaces.length > 0 ? `
${apiInterfaces.map((api, index) => `
#### 接口 ${index + 1}: ${api.name || '未命名接口'}

- **HTTP方法**: ${api.method || 'GET'}
- **接口路径**: ${api.path || '/api/unknown'}
- **接口描述**: ${api.description || '无描述'}

##### 入参参数
${api.input_parameters ? `
- **路径参数**: ${api.input_parameters.path_params ? api.input_parameters.path_params.join(', ') : '无'}
- **查询参数**: ${api.input_parameters.query_params ? api.input_parameters.query_params.join(', ') : '无'}
- **请求体参数**: ${api.input_parameters.body_params ? api.input_parameters.body_params.join(', ') : '无'}
` : '无参数信息'}

##### 返参结构
${api.output_parameters ? `
- **成功响应**: \`${api.output_parameters.success_response || '无'}\`
- **错误响应**: \`${api.output_parameters.error_response || '无'}\`
` : '无返参信息'}

##### 业务逻辑
${api.business_logic || '无业务逻辑说明'}
`).join('')}
` : '- 文档中暂未生成明确的接口设计\n- 建议查看AI分析详情或重新分析'}

### MQ消息队列配置
${mqConfiguration.topics && mqConfiguration.topics.length > 0 ? `
#### Topic配置
${mqConfiguration.topics.map((topic, index) => `
##### Topic ${index + 1}: ${topic.name || '未命名Topic'}
- **描述**: ${topic.description || '无描述'}
- **生产者**: ${topic.producer || '未指定'}
- **消费者**: ${topic.consumer || '未指定'}
`).join('')}

#### 客户端配置
${mqConfiguration.client_config ? `
- **服务器地址**: ${mqConfiguration.client_config.bootstrap_servers || '未配置'}
- **序列化方式**: ${mqConfiguration.client_config.serialization || '未指定'}
- **重试策略**: ${mqConfiguration.client_config.retry_policy || '未配置'}
` : '无客户端配置'}

#### 服务端配置
${mqConfiguration.server_config ? `
- **分区数量**: ${mqConfiguration.server_config.partition_count || '未配置'}
- **副本因子**: ${mqConfiguration.server_config.replication_factor || '未配置'}
- **保留策略**: ${mqConfiguration.server_config.retention_policy || '未配置'}
` : '无服务端配置'}
` : '- 暂未生成MQ配置\n- 建议查看AI分析详情或重新分析'}

### 技术规格说明
${technicalSpecs ? `
- **数据库设计**: ${technicalSpecs.database_design || '无设计建议'}
- **安全要求**: ${technicalSpecs.security_requirements || '无安全要求'}
- **性能考虑**: ${technicalSpecs.performance_considerations || '无性能要求'}
- **部署说明**: ${technicalSpecs.deployment_notes || '无部署说明'}
` : '无技术规格说明'}

### 实现优先级
${aiData.implementation_priority && aiData.implementation_priority.length > 0 ? 
  aiData.implementation_priority.map((item, index) => `${index + 1}. ${item}`).join('\n') : 
  '无优先级建议'}

### 系统集成点
${aiData.integration_points && aiData.integration_points.length > 0 ? 
  aiData.integration_points.map(point => `- ${point}`).join('\n') : 
  '无集成点说明'}

---

## 📊 分析总结

### 整体分析状态
- **已完成接口**: ${task.summary ? task.summary.completed_interfaces : 0}/${task.summary ? task.summary.total_interfaces : 3}
- **文档类型**: ${task.summary ? task.summary.document_type : '未知'}
- **复杂度等级**: ${task.summary ? task.summary.complexity_level : '中等'}
- **CRUD操作数**: ${task.summary ? task.summary.crud_operations_count : 0}
- **API接口数**: ${task.summary ? task.summary.api_interfaces_count : 0}
- **MQ Topic数**: ${task.summary ? task.summary.mq_topics_count : 0}
- **预估开发时间**: ${task.summary ? task.summary.estimated_development_time : '未知'}

### 数据流程
${task.data_flow ? `
1. **${task.data_flow.step1 || '文档解析'}**
2. **${task.data_flow.step2 || '内容分析'}**
3. **${task.data_flow.step3 || 'AI分析'}**
4. **${task.data_flow.integration || '结果整合'}**
` : '标准三步分析流程'}

### 分析模型信息
- **分析类型**: ${aiData.analysis_type || '综合分析'}
- **使用模型**: ${aiAnalysis.metadata ? aiAnalysis.metadata.analysis_model : '未知模型'}
- **置信度评分**: ${aiAnalysis.metadata && aiAnalysis.metadata.confidence_score ? (aiAnalysis.metadata.confidence_score * 100).toFixed(1) + '%' : 'N/A'}
- **分析时长**: ${aiAnalysis.metadata && aiAnalysis.metadata.analysis_duration ? aiAnalysis.metadata.analysis_duration.toFixed(2) + '秒' : '未知'}
- **分析成功**: ${aiAnalysis.metadata && aiAnalysis.metadata.success ? '✅ 是' : '❌ 否'}

---

## 🔗 技术信息

### 分析引擎
- **系统版本**: analyDesign v2.0
- **处理流程**: 文档解析 → 内容分析 → AI智能分析 → 三接口结果整合

### 接口调用情况
- **文档解析接口**: \`${documentParsing.endpoint || 'GET /api/file/parsing/N/A'}\` ${documentParsing.status === 'completed' ? '✅' : '⏳'}
- **内容分析接口**: \`${contentAnalysis.endpoint || 'POST /api/file/analyze/N/A'}\` ${contentAnalysis.status === 'completed' ? '✅' : '⏳'}
- **AI智能解析接口**: \`${aiAnalysis.endpoint || 'POST /api/file/ai-analyze/N/A'}\` ${aiAnalysis.status === 'completed' ? '✅' : '⏳'}
- **结果获取接口**: \`GET /api/file/result/${task.task_id || 'N/A'}\` ✅

### 接口处理时间
${task.timestamps ? `
- **任务创建**: ${task.timestamps.created_at ? new Date(task.timestamps.created_at).toLocaleString('zh-CN') : '未知'}
- **解析完成**: ${task.timestamps.parsing_completed ? new Date(task.timestamps.parsing_completed).toLocaleString('zh-CN') : '未完成'}
- **内容分析完成**: ${task.timestamps.content_analysis_completed ? new Date(task.timestamps.content_analysis_completed).toLocaleString('zh-CN') : '未完成'}
- **AI分析完成**: ${task.timestamps.ai_analysis_completed ? new Date(task.timestamps.ai_analysis_completed).toLocaleString('zh-CN') : '未完成'}
- **最后更新**: ${task.timestamps.updated_at ? new Date(task.timestamps.updated_at).toLocaleString('zh-CN') : '未知'}
` : '无时间戳信息'}

### 支持格式
- **文档格式**: Word (.docx), PDF (.pdf), 文本 (.txt), Markdown (.md)
- **输出格式**: JSON数据 + Markdown报告

### 生成信息
- **报告生成时间**: ${currentTime}
- **数据来源**: 三接口整合数据 (v2.0)
- **报告状态**: ${task.overall_status === 'completed' ? '✅ 完整分析' : '⚠️ 部分分析'}

---

*此报告由 analyDesign v2.0 智能分析系统基于文档解析、内容分析、AI智能解析三个接口整合数据自动生成*
`

    console.log('📝 Markdown报告生成完成 - 使用三接口整合数据结构 v2.0')
    return markdown
  }

  // 开始完整分析流程（V2版本）
  const startFullAnalysisV2 = async (file) => {
    try {
      isProcessing.value = true
      
      // 将文件转换为base64
      const fileContent = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target.result.split(',')[1]) // 去掉data:xxx;base64,前缀
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
      
      // 调用V2启动接口
      const response = await api.post('/api/v2/analysis/start', {
        file_info: {
          name: file.name,
          type: file.type,
          size: file.size,
          content: fileContent
        }
      })
      
      if (response.data.success) {
        const taskId = response.data.task_id
        
        // 创建任务对象
        const task = {
          id: taskId,
          fileName: file.name,
          fileType: file.type,
          fileSize: file.size,
          status: 'starting',
          progress: 0,
          description: '分析流程启动中',
          stages: response.data.stages,
          startTime: Date.now(),
          updatedAt: new Date()
        }
        
        // 更新状态
        currentParsingTask.value = task
        parsingTasks.value.set(taskId, task)
        
        // 初始化处理步骤（确保UI显示所有阶段）
        initProcessingStepsV2()
        
        // 开始轮询进度
        startProgressPolling(taskId)
        
        console.log(`🚀 V2 完整分析已启动: ${file.name}, 任务ID: ${taskId}`)
        
        return {
          success: true,
          taskId,
          message: '完整分析流程已启动'
        }
      } else {
        throw new Error(response.data.error || '启动分析失败')
      }
      
    } catch (error) {
      console.error('启动完整分析失败:', error)
      isProcessing.value = false
      
      ElMessage.error(`启动分析失败: ${error.message}`)
      
      return {
        success: false,
        error: error.message
      }
    }
  }
  
  // V2版本进度轮询
  const startProgressPolling = (taskId) => {
    console.log(`📊 开始V2进度轮询: ${taskId}`)
    
    let pollTimeout // 声明轮询定时器变量
    
    const pollProgress = async () => {
      try {
        // 更新当前进行中节点显示轮询状态
        updateCurrentNodeMessage('正在检查进度...')
        
        const response = await api.get(`/api/v2/analysis/progress/${taskId}`)
        
        if (response.data.success) {
          const progressData = response.data
          
                      // 轮询成功，清理轮询状态显示
            clearCurrentNodePollingMessage()
            
            // 更新任务状态
            updateTaskProgress(progressData)
            
            // 检查是否有错误
            if (progressData.error) {
              console.error('任务执行出错:', progressData.error)
              isProcessing.value = false
              ElMessage.error(`分析失败: ${progressData.error}`)
              return
            }
            
            // 增强的完成状态检查逻辑
            const stages = progressData.stages || {}
            const isAllStagesCompleted = stages.document_parsing?.status === 'completed' && 
                                       stages.content_analysis?.status === 'completed' && 
                                       stages.ai_analysis?.status === 'completed'
            
            const isCompleted = progressData.overall_status === 'completed' || 
                              progressData.overall_status === 'fully_completed' ||
                              progressData.current_stage === 'fully_completed' ||
                              progressData.overall_progress >= 100 ||
                              isAllStagesCompleted
            
            // 如果任务完成，停止轮询
            if (isCompleted) {
              console.log(`🎉 V2分析完成: ${taskId}`)
              isProcessing.value = false
              
              // 停止所有轮询
              stopPolling(taskId, 'all')
              
              // 获取最终结果（包含生成的markdown）
              console.log(`📡 准备获取最终结果...`)
              await fetchFinalResultV2(taskId)
              
              // 切换到解析结果页签
              setTimeout(() => {
                window.dispatchEvent(new CustomEvent('switchToResultsTab', {
                  detail: { tab: 'files' }
                }))
              }, 1000)
              
              return
            }
            
            // 检查是否失败
            if (progressData.overall_status === 'failed') {
              console.error(`❌ V2分析失败: ${taskId}`, progressData.error)
              isProcessing.value = false
              ElMessage.error(`分析失败: ${progressData.error || '未知错误'}`)
              return
            }
            
            // 继续轮询，根据当前进度调整间隔
            const hasRunningStage = Object.values(progressData.stages || {}).some(stage => stage.status === 'running')
            const interval = hasRunningStage ? 2000 : 5000 // 有运行中的阶段时更频繁轮询
            
            pollTimeout = setTimeout(pollProgress, interval)
        } else {
          console.error('获取进度失败:', response.data.error)
          
          // 显示错误信息
          updateCurrentNodeMessage(`获取进度失败: ${response.data.error}`)
          
          // 如果是404错误，任务可能不存在，停止轮询
          if (response.status === 404) {
            console.log('任务不存在，停止轮询')
            return
          }
          
          // 其他错误继续轮询
          pollTimeout = setTimeout(pollProgress, 5000)
        }
      } catch (error) {
        console.error('轮询进度失败:', error)
        
        // 显示网络错误信息
        updateCurrentNodeMessage('网络错误，正在重试...')
        
        // 网络错误等，继续轮询但降低频率
        pollTimeout = setTimeout(pollProgress, 5000)
      }
    }
    
    pollProgress()
  }
  
  // 更新当前进行中节点的message显示
  const updateCurrentNodeMessage = (pollingMessage) => {
    Object.keys(nodeProgress.value).forEach(stageName => {
      const node = nodeProgress.value[stageName]
      if (node.status === 'running') {
        // 保存原始message（如果还没保存的话）
        if (!node.originalMessage) {
          node.originalMessage = node.message
        }
        // 更新显示的message
        node.message = `${node.originalMessage} (${pollingMessage})`
      }
    })
  }
  
  // 清理当前节点的轮询信息显示
  const clearCurrentNodePollingMessage = () => {
    Object.keys(nodeProgress.value).forEach(stageName => {
      const node = nodeProgress.value[stageName]
      if (node.originalMessage) {
        // 恢复原始message
        node.message = node.originalMessage
        delete node.originalMessage
      }
    })
  }
  
  // 更新节点进度状态
  const updateNodeProgress = (stages) => {
    if (!stages) return
    
    // 更新三个阶段的进度
    Object.keys(stages).forEach(stageName => {
      const stage = stages[stageName]
      
      if (nodeProgress.value[stageName]) {
        // 如果状态发生变化，清理轮询状态
        if (nodeProgress.value[stageName].status !== stage.status && nodeProgress.value[stageName].originalMessage) {
          nodeProgress.value[stageName].message = nodeProgress.value[stageName].originalMessage
          delete nodeProgress.value[stageName].originalMessage
        }
        
        nodeProgress.value[stageName].progress = stage.progress || 0
        nodeProgress.value[stageName].message = stage.message || ''
        nodeProgress.value[stageName].status = stage.status || 'pending'
        
        // 设置是否可以开始
        if (stage.status === 'pending' && stageName === 'document_parsing') {
          nodeProgress.value[stageName].canStart = true
        } else if (stage.status === 'pending' && stageName === 'content_analysis' && 
                   stages.document_parsing?.status === 'completed') {
          nodeProgress.value[stageName].canStart = true
        } else if (stage.status === 'pending' && stageName === 'ai_analysis' && 
                   stages.content_analysis?.status === 'completed') {
          nodeProgress.value[stageName].canStart = true
        } else {
          nodeProgress.value[stageName].canStart = false
        }
      }
    })
  }
  
  // V2版本：初始化处理步骤
  const initProcessingStepsV2 = () => {
    // 清空之前的步骤
    clearProcessingSteps()
    
    // 创建所有处理步骤
    const steps = [
      {
        id: 'step_upload',
        title: '文档上传',
        description: '文档上传完成',
        status: 'success',
        progress: 100,
        timestamp: new Date().toLocaleTimeString()
      },
      {
        id: 'step_parsing',
        title: '文档解析',
        description: '准备开始文档解析...',
        status: 'pending',
        progress: 0,
        timestamp: new Date().toLocaleTimeString()
      },
      {
        id: 'step_content_analysis',
        title: '内容分析',
        description: '等待文档解析完成...',
        status: 'pending',
        progress: 0,
        timestamp: new Date().toLocaleTimeString()
      },
      {
        id: 'step_ai_analysis',
        title: 'AI智能分析',
        description: '等待内容分析完成...',
        status: 'pending',
        progress: 0,
        timestamp: new Date().toLocaleTimeString()
      },
      {
        id: 'step_document_generation',
        title: '生成文档',
        description: '等待AI分析完成...',
        status: 'pending',
        progress: 0,
        timestamp: new Date().toLocaleTimeString()
      }
    ]
    
    steps.forEach(step => addProcessingStep(step))
    console.log('🔄 V2处理步骤已初始化')
  }
  
  // V2版本：更新处理步骤（兼容老的UI系统）
  const updateProcessingStepsV2 = (stages, currentStage) => {
    if (!stages) return
    
    // 映射关系：后端阶段名 -> 前端步骤ID
    const stageMapping = {
      'document_parsing': 'step_parsing',
      'content_analysis': 'step_content_analysis', 
      'ai_analysis': 'step_ai_analysis',
      'document_generation': 'step_document_generation'
    }
    
    // 标题映射
    const titleMapping = {
      'document_parsing': '文档解析',
      'content_analysis': '内容分析',
      'ai_analysis': 'AI智能分析',
      'document_generation': '生成文档'
    }
    
    // 更新各个阶段的步骤
    Object.keys(stages).forEach(stageName => {
      const stage = stages[stageName]
      const stepId = stageMapping[stageName]
      
      if (stepId) {
        let stepStatus = 'pending'
        if (stage.status === 'running') {
          stepStatus = 'primary'
        } else if (stage.status === 'completed') {
          stepStatus = 'success'
        } else if (stage.status === 'failed') {
          stepStatus = 'danger'
        }
        
        updateProcessingStep({
          id: stepId,
          title: titleMapping[stageName] || stageName,
          description: stage.message || `${titleMapping[stageName]}中...`,
          status: stepStatus,
          progress: stage.progress || 0,
          timestamp: new Date().toLocaleTimeString()
        })
      }
    })
    
    console.log(`🔄 V2处理步骤已更新，当前阶段: ${currentStage}`)
  }
  
  // 生成Markdown内容
  const generateMarkdownContent = (resultData) => {
    if (!resultData) return ''
    
    let markdown = '# 开发指导设计方案\n\n'
    
    // 内容分析结果
    if (resultData.content_analysis) {
      markdown += '## 🔍 内容分析\n\n'
      markdown += resultData.content_analysis + '\n\n'
    }
    
    // AI分析结果
    if (resultData.ai_analysis) {
      markdown += '## 🤖 AI智能分析\n\n'
      markdown += resultData.ai_analysis + '\n\n'
    }
    
    return markdown
  }
  
  // 获取最终分析结果（V2版本，包含后端生成的markdown）
  const fetchFinalResultV2 = async (taskId) => {
    try {
      console.log(`📡 正在获取最终分析结果: ${taskId}`)
      
      const response = await api.get(`/api/file/result/${taskId}`)
      
      console.log('📄 API响应状态:', response.status)
      console.log('📄 API响应头:', response.headers)
      console.log('📄 获取到的原始响应:', response)
      console.log('📄 响应数据类型:', typeof response.data)
      console.log('📄 响应数据内容:', response.data)
      
      // 检查响应是否为空
      if (!response.data) {
        throw new Error('API返回的数据为空')
      }
      
      // 检查是否有success字段
      if (response.data.success === false) {
        const errorMsg = response.data.error || response.data.message || '未知API错误'
        throw new Error(`API调用失败: ${errorMsg}`)
      }
      
      // 检查是否有data字段
      if (!response.data.success || !response.data.data) {
        console.warn('⚠️ API响应格式不符合预期:', response.data)
        
        // 尝试直接使用响应数据
        const resultData = response.data.data || response.data
        if (!resultData) {
          throw new Error('API返回的数据中没有找到结果数据')
        }
        
        console.log('📊 使用备选数据结构:', resultData)
      }
      
      const resultData = response.data.data || response.data
      console.log('📊 最终使用的结果数据:', resultData)
      
      // 提取各个接口的数据
      const documentParsing = resultData.document_parsing || {}
      const contentAnalysis = resultData.content_analysis || {}
      const aiAnalysis = resultData.ai_analysis || {}
      
      console.log('📊 接口数据解析:')
      console.log('  - documentParsing:', documentParsing)
      console.log('  - contentAnalysis:', contentAnalysis)
      console.log('  - aiAnalysis:', aiAnalysis)
      
      // 提取文档内容 - 从多个可能的位置获取
      let documentContent = ''
      
      // 尝试从文档解析结果获取内容
      const docParsingData = documentParsing.data || documentParsing
      if (docParsingData.textContent?.textBlocks) {
        documentContent = docParsingData.textContent.textBlocks
          .map(block => block.content)
          .join('\n')
          .replace(/\r/g, '') // 移除回车符
      } else if (docParsingData.content || docParsingData.text_content) {
        documentContent = docParsingData.content || docParsingData.text_content
      }
      
      console.log('📄 提取的文档内容长度:', documentContent.length)
      
      // 提取内容分析结果
      const contentAnalysisData = contentAnalysis.data || contentAnalysis
      console.log('📊 内容分析数据:', contentAnalysisData)
      
      // 提取AI分析结果  
      const aiAnalysisData = aiAnalysis.data || aiAnalysis
      console.log('🤖 AI分析数据:', aiAnalysisData)
      
      // 生成或使用后端提供的markdown内容
      let markdownContent = resultData.markdown_content
      if (!markdownContent && resultData.interfaces) {
        console.log('📝 后端未提供markdown，使用前端生成')
        markdownContent = generateMarkdownReport(resultData)
      }
      
      console.log('📝 Markdown内容长度:', markdownContent?.length || 0)
      
      // 设置完整的分析结果
      // 从多个来源提取文件信息
      const basicInfo = resultData.basic_info || {}
      const docParsingInfo = documentParsing.data || documentParsing
      const fileFormatInfo = docParsingInfo.fileFormat || {}
      const metadataInfo = docParsingInfo.metadata?.documentInfo || {}
      
      // 提取文件名 - 优先使用文档标题，回退到其他来源
      let fileName = metadataInfo.title || 
                    basicInfo.filename || 
                    basicInfo.name || 
                    'test_requirements.txt'  // 从上传的文件名获取
      
      // 清理文件名中的特殊字符
      fileName = fileName.replace(/\r|\n/g, '').trim()
      
      // 提取文件类型
      const fileType = fileFormatInfo.subType || 
                      fileFormatInfo.primaryType || 
                      basicInfo.file_type || 
                      'txt'
      
      // 提取文件大小 - 从文档解析结果获取实际大小
      const fileSize = fileFormatInfo.basicInfo?.fileSize || 
                      docParsingInfo.fileFormat?.technicalDetails?.charCount || 
                      0
      
      // 提取字符数
      const characterCount = docParsingInfo.fileFormat?.technicalDetails?.charCount || 
                            docParsingInfo.textContent?.paragraphs || 
                            documentContent.length
      
      console.log('📄 文件基本信息:', { 
        fileName, 
        fileType, 
        fileSize, 
        characterCount,
        basicInfo, 
        fileFormatInfo,
        metadataInfo 
      })
      
      // 辅助函数：格式化文件大小
      const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 B'
        const k = 1024
        const sizes = ['B', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
      }
      
      const analysisResultData = {
        title: `📄 ${fileName} - 分析报告`,
        type: 'comprehensive', 
        timestamp: Date.now(),
        fileInfo: {
          name: fileName,
          type: fileType,
          size: typeof fileSize === 'string' ? fileSize : formatFileSize(fileSize)
        },
        details: {
          type: fileType,
          length: documentContent.length,
          parsing_duration: documentParsing.processing_time || 0
        },
        content: documentContent,
        // 直接传递后端返回的fileFormat和documentStructure数据
        fileFormat: docParsingInfo.fileFormat || {},
        documentStructure: docParsingInfo.documentStructure || {},
        notes: docParsingInfo.notes || resultData.notes || '',
        contentAnalysis: {
          document_type: contentAnalysisData.document_type || metadataInfo.documentType || 'unknown',
          language: fileFormatInfo.basicInfo?.language || contentAnalysisData.language || 'zh',
          summary: contentAnalysisData.summary || metadataInfo.description || '',
          keyword_extraction: contentAnalysisData.keywords || docParsingInfo.contentKeyWord?.primaryKeywords || [],
          statistics: {
            character_count: characterCount,
            word_count: fileFormatInfo.technicalDetails?.wordCount || contentAnalysisData.word_count || 0
          },
          structure_analysis: contentAnalysisData.structure_analysis || docParsingInfo.documentStructure || {},
          requirements_analysis: contentAnalysisData.crud_analysis || {},
          // 添加变更分析结果支持
          change_analysis: contentAnalysisData.change_analysis || null,
          metadata: contentAnalysisData.metadata || null
        },
        aiAnalysis: {
          analysis_type: 'comprehensive',
          analysis_model: 'Doubao',
          confidence_score: 0.95,
          analyzed_at: Date.now(),
          analysis_duration: aiAnalysis.processing_time || 0,
          ai_response: aiAnalysisData.analysis_result || aiAnalysisData.ai_response || '分析完成',
          custom_prompt: aiAnalysisData.custom_prompt || ''
        },
        analysisSummary: resultData.analysis_summary || '',
        markdownContent: markdownContent
      }
      
      console.log('📊 构建的分析结果对象:', analysisResultData)
      
      setAnalysisResult(analysisResultData)
      
      console.log('✅ V2最终分析结果已设置（包含markdown）')
      
      // 显示成功消息
      ElMessage.success('分析完成！结果已更新')
      
    } catch (error) {
      console.error('❌ 获取V2最终结果详细错误:', {
        error: error,
        message: error.message,
        stack: error.stack,
        name: error.name
      })
      
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.message || 
                          error.message || 
                          '网络请求失败'
      
      console.error('❌ 处理后的错误信息:', errorMessage)
      ElMessage.error(`获取分析结果失败: ${errorMessage}`)
      
      // 设置错误状态
      setAnalysisResult({
        title: '获取结果失败',
        type: 'error',
        timestamp: Date.now(),
        error: errorMessage,
        content: `获取分析结果时发生错误: ${errorMessage}`
      })
    }
  }

  // 获取最终分析结果
  const fetchFinalResult = async (taskId) => {
    try {
      const response = await api.get(`/api/file/result/${taskId}`)
      
      if (response.data.success && response.data.data) {
        const resultData = response.data.data
        
        // 生成Markdown内容
        const markdownContent = generateMarkdownContent(resultData)
        
        // 设置完整的分析结果
        setAnalysisResult({
          title: `📄 ${resultData.basic_info?.filename || '未知文件'} - 分析报告`,
          type: 'comprehensive',
          timestamp: Date.now(),
          fileInfo: resultData.basic_info,
          documentParsing: resultData.document_parsing,
          contentAnalysis: resultData.content_analysis,
          aiAnalysis: resultData.ai_analysis,
          analysisSummary: resultData.analysis_summary,
          markdownContent: markdownContent
        })
        
        console.log('📄 最终分析结果已设置')
      }
      
    } catch (error) {
      console.error('获取最终结果失败:', error)
    }
  }

  // 更新任务进度状态
  const updateTaskProgress = (progressData) => {
    if (currentParsingTask.value && currentParsingTask.value.id === progressData.task_id) {
      currentParsingTask.value.status = progressData.current_stage
      currentParsingTask.value.progress = progressData.overall_progress
      currentParsingTask.value.stages = progressData.stages
      currentParsingTask.value.overallStatus = progressData.overall_status
      currentParsingTask.value.error = progressData.error
      currentParsingTask.value.updatedAt = new Date()
      
      // 更新节点进度状态
      updateNodeProgress(progressData.stages)
      
      // 更新处理步骤显示（兼容老的UI系统）
      updateProcessingStepsV2(progressData.stages, progressData.current_stage)
      
      console.log(`📊 V2进度更新: ${progressData.current_stage}, 整体进度: ${progressData.overall_progress}%`)
    }
  }

  return {
    // 状态
    socket,
    isConnected,
    messages,
    currentMessage,
    isTyping,
    clientId,
    sessionId,
    
    // 文件解析相关状态
    parsingTasks,
    currentParsingTask,
    parsingProgress,
    parsingStatus,
    isProcessing,
    
    // 处理步骤
    processingSteps,
    currentProcessing,
    analysisResult,
    nodeProgress,
    
    // 添加轮询管理
    activePolls,
    
    // 计算属性
    lastMessage,
    isFileProcessing,
    
    // 方法
    connect,
    disconnect,
    sendMessage,
    addMessage,
    clearMessages,
    addProcessingStep,
    updateProcessingStep,
    clearProcessingSteps,
    setCurrentProcessing,
    setAnalysisResult,
    clearAnalysisResult,
    checkHealth,
    getSessions,
    uploadFile,
    getParsingStatus,
    fileToBase64,
    resetParsingState,
    startContentAnalysis,
    startAIAnalysis,
    getUploadedFiles,
    deleteUploadedFile,
    stopPolling,
    setPollingTimer,
    clearAllPolling,
    updateSessionId,
    // 导出工具函数
    generateMessageId: () => generateMessageId(),
    generateClientId: () => generateClientId(),
    generateSessionId: () => generateSessionId(),
    // 导出Markdown生成函数
    generateMarkdownReport,
    generateMarkdownContent,
    startFullAnalysisV2,
    startProgressPolling,
    updateNodeProgress,
    initProcessingStepsV2,
    updateProcessingStepsV2,
    fetchFinalResult,
    fetchFinalResultV2,
  }
}) 