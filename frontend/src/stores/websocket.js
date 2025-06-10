import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

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
    console.log('收到响应:', response.status, response.data)
    return response
  },
  (error) => {
    // 只在非网络连接错误时输出错误信息
    if (error.code !== 'ECONNREFUSED' && error.code !== 'ERR_NETWORK') {
      console.error('响应错误:', error.response?.status, error.response?.data || error.message)
    } else {
      console.warn('网络连接失败，请检查后端服务是否启动')
    }
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
  
  // 处理步骤
  const processingSteps = ref([])
  const currentProcessing = ref(null)
  const analysisResult = ref(null)
  
  // 轮询管理
  const activePolls = ref(new Map())

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

  // 连接WebSocket服务器 (Socket.IO) - 支持任务级连接
  const connect = (taskId = null) => {
    try {
      // 动态导入socket.io-client
      import('socket.io-client').then(({ io }) => {
        const wsUrl = 'http://localhost:8081'
        console.log('🔌 正在连接Socket.IO服务器:', wsUrl)
        
        // 🔧 新架构：支持使用TaskID作为连接参数 + 禁用缓冲优化
        const connectOptions = {
          timeout: 20000,  // 减少超时时间
          transports: ['websocket'],  // 强制使用websocket，避免polling缓冲
          forceNew: !!taskId,  // 任务级连接强制新建
          upgrade: false,    // 禁用传输升级避免切换延迟
          rememberUpgrade: false,  // 禁用升级记忆
          reconnection: !taskId,     // 任务级连接不自动重连
          reconnectionAttempts: taskId ? 0 : 3,  // 减少重连次数
          reconnectionDelay: 500,   // 减少重连延迟
          reconnectionDelayMax: 2000, // 减少最大重连延迟
          pingTimeout: 10000,     // 大幅减少ping超时（10秒）
          pingInterval: 5000,     // 大幅减少ping间隔（5秒）
          // 🔥 关键：禁用各种缓冲和优化
          autoConnect: true,
          multiplex: false,       // 禁用多路复用避免缓冲
          randomizationFactor: 0, // 禁用随机化
          query: taskId ? { task_id: taskId } : {}  // 传递TaskID
        }
        
        console.log('🔧 连接配置:', connectOptions)
        console.log('🆔 任务级连接ID:', taskId || '通用连接')
        
        socket.value = io(wsUrl, connectOptions)
        
        socket.value.on('connect', () => {
          isConnected.value = true
          console.log('✅ Socket.IO 连接成功')
          console.log('🆔 前端客户端ID:', clientId.value)
          console.log('🆔 Socket.IO会话ID:', socket.value.id)
          console.log('📋 ID映射说明: 前端显示ID为标识用，实际通信使用Socket.IO会话ID')
          console.log('⏰ 连接时间:', new Date().toLocaleTimeString())
          
          // 检查是否有进行中的任务
          checkOngoingTasks()
          
          // 🔧 新增：启动Session一致性监控
          startSessionConsistencyMonitoring()
          
          // 添加欢迎消息
          addMessage({
            type: 'chat_response',
            message: '您好！我是智能需求分析助手，可以帮您分析需求文档。请上传您的文档开始分析，或者直接与我对话。',
            timestamp: Date.now(),
            message_id: generateMessageId()
          })
        })
        
        socket.value.on('connected', (data) => {
          console.log('📨 收到连接确认:', data)
          console.log('🔍 ID对比:')
          console.log('  前端生成ID:', clientId.value)
          console.log('  后端返回ID:', data.client_id)
          console.log('  Socket.IO ID:', socket.value.id)
          console.log('📋 说明: 后端使用Socket.IO ID进行通信路由')
          console.log('🔧 [调试] 确认analysis_progress事件监听器已设置')
          handleWebSocketMessage(data)
        })
        
        // 专门监听 analysis_progress 事件
        socket.value.on('analysis_progress', (data) => {
          console.log('🎯 [专门监听器] 收到分析进度更新:', data)
          console.log('🎯 [专门监听器] 进度数据结构:', JSON.stringify(data, null, 2))
          console.log('🎯 [专门监听器] 调用 handleAnalysisProgress...')
          try {
            handleAnalysisProgress(data)
            console.log('🎯 [专门监听器] handleAnalysisProgress 执行完成')
          } catch (error) {
            console.error('❌ [专门监听器] handleAnalysisProgress 执行失败:', error)
          }
        })
        
        // 添加专门的事件监听器
        socket.value.on('session_mapping_updated', (data) => {
          console.log('✅ Session ID映射更新确认:', data)
          console.log('🔄 更新后的Session ID:', data.new_session_id)
          console.log('🆔 当前Socket ID:', socket.value.id)
        })
        
        socket.value.on('session_mapping_error', (data) => {
          console.error('❌ Session ID映射更新失败:', data)
        })

        // 🔧 新增：任务绑定确认监听
        socket.value.on('task_binding_confirmed', (data) => {
          console.log('✅ 收到任务绑定确认:', data)
          console.log('🎯 强绑定建立成功 - TaskID:', data.task_id, 'SessionID:', data.session_id)
        })
        
        socket.value.on('task_binding_error', (data) => {
          console.error('❌ 任务绑定失败:', data)
        })

        // 🔧 新增：任务完成断开事件监听
        socket.value.on('task_completed_disconnect', (data) => {
          console.log('🏁 收到任务完成断开通知:', data)
          const taskId = data.task_id
          
          // 更新任务状态为已完成
          if (parsingTasks.value.has(taskId)) {
            const task = parsingTasks.value.get(taskId)
            task.status = 'completed'
            task.completedAt = new Date()
            parsingTasks.value.set(taskId, task)
          }
          
          // 设置完成状态
          parsingStatus.value = 'completed'
          
          console.log(`✅ [任务完成] 任务 ${taskId} 已完成，连接将自动断开`)
        })

        // 监听所有事件用于调试
        socket.value.onAny((eventName, ...args) => {
          console.log('📨 [onAny] 收到Socket.IO事件:', eventName, args)
          
          // 特别检查analysis_progress事件
          if (eventName === 'analysis_progress') {
            console.log('🎯 [onAny] 检测到analysis_progress事件！')
            console.log('🎯 [onAny] 事件数据:', JSON.stringify(args[0], null, 2))
            console.log('🎯 [onAny] 专门监听器是否存在:', typeof socket.value._callbacks?.['analysis_progress'])
            console.log('🎯 [onAny] 强制调用handleAnalysisProgress进行应急处理')
            handleAnalysisProgress(args[0])
            return
          }
          
          // 特殊事件也跳过
          if (eventName === 'session_mapping_updated' || eventName === 'session_mapping_error' || eventName === 'task_completed_disconnect') {
            console.log('🎯 特殊事件已由专门监听器处理:', eventName)
            return
          }
          
          if (eventName !== 'connect' && eventName !== 'connected') {
            // 检查是否是包含进度信息的其他事件
            const data = args[0]
            if (data && (data.overall_progress !== undefined || data.stage_progress)) {
              console.log('🎯 发现包含进度信息的其他事件:', eventName, data)
              handleAnalysisProgress(data)
            } else {
              handleWebSocketMessage({ type: eventName, ...args[0] })
            }
          }
        })
        
        socket.value.on('disconnect', (reason) => {
          isConnected.value = false
          console.log('❌ Socket.IO 连接已断开，原因:', reason)
          console.log('⏰ 断开时间:', new Date().toLocaleTimeString())
          console.log('📊 断开前的Session ID:', socket.value?.id || 'N/A')
          
          // 🔧 新增：停止Session一致性监控
          stopSessionConsistencyMonitoring()
        })
        
        // 监听连接错误
        socket.value.on('error', (error) => {
          console.error('❌ Socket.IO 错误:', error)
          console.log('⏰ 错误时间:', new Date().toLocaleTimeString())
        })
        
        // 监听重连事件
        socket.value.on('reconnect', (attemptNumber) => {
          console.log('🔄 Socket.IO 重新连接成功，尝试次数:', attemptNumber)
          console.log('⏰ 重连时间:', new Date().toLocaleTimeString())
          console.log('🆔 重连后的新Session ID:', socket.value.id)
          isConnected.value = true
          
          // 🔧 新增：自动同步所有进行中任务的Session映射
          console.log('🔄 [Session映射] 开始同步重连后的Session映射...')
          
          // 检查当前进行中的任务
          for (const [taskId, task] of parsingTasks.value.entries()) {
            if (task.status !== 'completed' && task.status !== 'failed') {
              console.log(`🔄 [Session映射] 同步任务 ${taskId} 的Session映射`)
              console.log(`  旧SessionID: ${task.currentSessionId}`)
              console.log(`  新SessionID: ${socket.value.id}`)
              
              // 更新任务的SessionID
              task.currentSessionId = socket.value.id
              parsingTasks.value.set(taskId, task)
              
              // 发送Session映射更新到后端
              const syncMessage = {
                task_id: taskId,
                new_session_id: socket.value.id,
                old_session_id: task.initialSessionId,
                client_type: 'frontend',
                action: 'reconnect_sync'
              }
              
              console.log(`📡 [Session映射] 发送重连同步消息:`, syncMessage)
              socket.value.emit('update_session_mapping', syncMessage)
            }
          }
          
          // 如果有当前正在处理的任务，请求最新进度
          if (currentParsingTask.value && currentParsingTask.value.id) {
            setTimeout(() => {
              console.log('🔄 [Session映射] 请求最新任务进度:', currentParsingTask.value.id)
              socket.value.emit('get_analysis_progress', {
                task_id: currentParsingTask.value.id
              })
            }, 1000)
          }
        })
        
        socket.value.on('reconnect_attempt', (attemptNumber) => {
          console.log('🔄 尝试重新连接 Socket.IO，第', attemptNumber, '次')
          console.log('⏰ 重连尝试时间:', new Date().toLocaleTimeString())
        })
        
        socket.value.on('connect_error', (error) => {
          console.warn('⚠️ Socket.IO 连接失败:', error.message)
          console.log('⏰ 连接失败时间:', new Date().toLocaleTimeString())
          isConnected.value = false
          // 降级到HTTP模式
          initHttpMode()
        })
        
      }).catch((error) => {
        console.error('导入socket.io-client失败:', error)
        initHttpMode()
      })
      
    } catch (error) {
      console.error('连接失败:', error)
      isConnected.value = false
      // 降级到HTTP模式
      initHttpMode()
    }
  }

  // Socket.IO连接失败时的处理
  const initHttpMode = () => {
    console.log('❌ Socket.IO连接失败')
    isConnected.value = false
    
    // 添加错误提示消息
    addMessage({
      type: 'chat_response',
      message: '⚠️ 无法连接到WebSocket服务器。请确保后端服务已启动（端口8081和8082）。\n\n您仍可以进行聊天，但文档分析功能将不可用。\n\n启动后端服务的方法：\n1. 打开终端\n2. 进入项目目录\n3. 运行: python run.py --mode=full',
      timestamp: Date.now(),
      message_id: generateMessageId()
    })
  }

  // 处理分析进度更新
  const handleAnalysisProgress = (data) => {
    console.log('📊 [handleAnalysisProgress] 开始处理分析进度:', data)
    console.log('📊 [handleAnalysisProgress] 当前 parsingProgress.value:', parsingProgress.value)
    
    if (!data.task_id) {
      console.warn('❌ [handleAnalysisProgress] 没有task_id，跳过处理')
      return
    }
    
    console.log('📊 [handleAnalysisProgress] 任务ID确认:', data.task_id)
    
    // 更新整体进度
    if (data.overall_progress !== undefined) {
      console.log(`📄 [整体进度] 更新: ${parsingProgress.value} -> ${data.overall_progress}%`)
      const oldProgress = parsingProgress.value
      parsingProgress.value = data.overall_progress
      console.log(`📄 [整体进度] 更新后: ${parsingProgress.value}%`)
      console.log(`📄 [整体进度] 验证更新: ${oldProgress} -> ${parsingProgress.value}`)
      
      // 同时更新currentProcessing对象，用于UI显示
      if (currentProcessing.value) {
        currentProcessing.value = {
          ...currentProcessing.value,
          progress: data.overall_progress,
          description: data.message || currentProcessing.value.description
        }
        console.log(`📄 更新currentProcessing进度: ${data.overall_progress}%`)
      } else {
        // 如果没有currentProcessing，创建一个
        setCurrentProcessing({
          description: data.message || '正在处理文档分析...',
          progress: data.overall_progress,
          status: 'primary'
        })
        console.log(`📄 创建新的currentProcessing，进度: ${data.overall_progress}%`)
      }
    }
    
    // 更新各阶段进度
    if (data.stage_progress) {
      const stageMapping = {
        'document_parsing': 'step_parsing',
        'content_analysis': 'step_content_analysis',
        'ai_analysis': 'step_ai_analysis'
      }
      
      const stageNames = {
        'document_parsing': '文档解析',
        'content_analysis': '内容分析',
        'ai_analysis': '智能解析'
      }
      
      for (const [stage, progress] of Object.entries(data.stage_progress)) {
        const stepId = stageMapping[stage]
        const stageName = stageNames[stage]
        
        console.log(`🔍 [阶段进度] 处理阶段: ${stage} -> ${stepId} (${stageName}) - ${progress}%`)
        console.log(`🔍 [阶段进度] 映射检查 - stepId: '${stepId}', stageName: '${stageName}'`)
        
        if (stepId) {
          let status = 'primary'
          let description = '正在处理...'
          
          if (progress === 100) {
            status = 'success'
            description = '已完成'
          } else if (progress > 0) {
            status = 'primary'
            description = `正在进行 ${progress}%`
          }
          
          console.log(`📄 调用 updateProcessingStep:`, {
            id: stepId,
            title: stageName,
            description: description,
            status: status,
            progress: progress
          })
          
          updateProcessingStep({
            id: stepId,
            title: stageName,
            description: description,
            status: status,
            progress: progress,
            timestamp: new Date().toLocaleTimeString()
          })
          
          console.log(`📄 更新阶段进度: ${stageName} ${progress}%`)
        } else {
          console.warn(`❌ 未找到阶段映射: ${stage}`)
        }
      }
    }
    
    // 检查是否完成
    if (data.status === 'completed') {
      parsingStatus.value = 'completed'
      updateProcessingStep({
        id: 'step_complete',
        title: '完成处理',
        description: '文档分析已完成',
        status: 'success',
        progress: 100,
        timestamp: new Date().toLocaleTimeString()
      })
    }
  }

  // 检查进行中的任务
  const checkOngoingTasks = async () => {
    try {
      console.log('🔍 检查进行中的任务...')
      const response = await api.get('/api/v2/analysis/tasks?limit=10')
      const data = response.data
      
      if (data.success && data.tasks && data.tasks.length > 0) {
        // 查找状态为running的任务
        const activeTask = data.tasks.find(task => task.status === 'running' || task.status === 'processing')
        
        if (activeTask) {
          console.log('📋 发现活跃任务:', activeTask)
          
          // 恢复任务状态
          if (activeTask.overall_progress !== undefined) {
            parsingProgress.value = activeTask.overall_progress
            parsingStatus.value = activeTask.status || 'running'
            
            // 创建或更新currentProcessing状态
            setCurrentProcessing({
              description: `正在处理: ${activeTask.file_name || activeTask.task_id || '文档分析'}`,
              progress: activeTask.overall_progress,
              status: 'primary'
            })
            
            console.log(`🔄 恢复任务状态: ${activeTask.overall_progress}% - ${activeTask.status}`)
            
            // 如果有阶段进度，也要恢复
            if (activeTask.stage_progress) {
              handleAnalysisProgress({
                task_id: activeTask.task_id,
                overall_progress: activeTask.overall_progress,
                stage_progress: activeTask.stage_progress,
                status: activeTask.status,
                message: `恢复任务: ${activeTask.file_name || '文档分析'}`
              })
            }
          }
        } else {
          console.log('📋 没有发现运行中的任务')
        }
      } else {
        console.log('📋 没有发现任何任务')
      }
    } catch (error) {
      console.log('🔍 检查活跃任务失败:', error.message)
      // 忽略错误，继续正常运行
    }
  }

  // 处理WebSocket消息
  const handleWebSocketMessage = (data) => {
    console.log('🔥 [WebSocket] 处理消息:', data.type || 'analysis_progress', data)
    
    switch (data.type) {
      case 'analysis_started':
        // 分析开始
        console.log('🚀 分析已开始:', data)
        parsingStatus.value = 'running'
        
        // 创建初始处理状态
        setCurrentProcessing({
          description: `开始分析任务: ${data.task_id}`,
          progress: 0,
          status: 'primary'
        })
        
        addMessage({
          type: 'chat_response',
          message: '✅ 文档分析已开始，正在处理...',
          timestamp: Date.now(),
          message_id: generateMessageId()
        })
        break
        
      case 'analysis_progress':
        // 分析进度更新
        if (data.task_id && data.progress !== undefined) {
          console.log(`📄 分析进度: ${data.progress}% - ${data.message}`)
          
          // 更新对应的处理步骤
          if (data.stage) {
            updateProcessingStep({
              id: `step_${data.stage}`,
              title: data.stage_name || data.stage,
              description: data.message || '正在处理...',
              status: data.progress === 100 ? 'success' : 'primary',
              progress: data.progress,
              timestamp: new Date().toLocaleTimeString()
            })
          }
          
          // 更新全局进度
          parsingProgress.value = data.progress
        }
        break
        
      case 'stage_completed':
        // 阶段完成
        console.log(`✅ 阶段完成: ${data.stage}`)
        updateProcessingStep({
          id: `step_${data.stage}`,
          title: data.stage_name || data.stage,
          description: data.message || '已完成',
          status: 'success',
          progress: 100,
          timestamp: new Date().toLocaleTimeString()
        })
        break
        
      case 'analysis_completed':
        // 分析完成
        console.log('🎉 分析完成!')
        parsingStatus.value = 'completed'
        
        if (data.result) {
          setAnalysisResult(data.result)
        }
        
        updateProcessingStep({
          id: 'step_complete',
          title: '完成处理',
          description: '文档分析已完成',
          status: 'success',
          progress: 100,
          timestamp: new Date().toLocaleTimeString()
        })
        
        addMessage({
          type: 'chat_response',
          message: '文档分析已完成！您可以在"需求文档分析"标签页查看结果。',
          timestamp: Date.now(),
          message_id: generateMessageId()
        })
        break
        
      case 'analysis_failed':
        // 分析失败
        console.log('❌ 分析失败:', data.error)
        parsingStatus.value = 'failed'
        
        updateProcessingStep({
          id: data.stage ? `step_${data.stage}` : 'step_error',
          title: '分析失败',
          description: data.error || '未知错误',
          status: 'error',
          progress: 0,
          timestamp: new Date().toLocaleTimeString()
        })
        
        addMessage({
          type: 'chat_response',
          message: `分析失败：${data.error || '未知错误'}`,
          timestamp: Date.now(),
          message_id: generateMessageId()
        })
        break
        
      case 'chat_response':
        // 聊天回复
        if (data.message) {
          addMessage({
            type: 'chat_response',
            message: data.message,
            timestamp: Date.now(),
            message_id: generateMessageId(),
            analysis: data.analysis
          })
        }
        break
        
      default:
        console.log('🔶 未知的WebSocket消息类型:', data.type)
    }
  }

  // 断开连接
  const disconnect = () => {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
    }
    isConnected.value = false
    console.log('Socket.IO 连接已断开')
  }

  // 🔧 新增：任务级连接管理
  const connectForTask = async (taskId) => {
    console.log('🎯 为任务创建专用WebSocket连接:', taskId)
    
    // 如果已有连接，先断开
    if (socket.value && socket.value.connected) {
      console.log('🔄 断开现有连接以建立任务专用连接')
      socket.value.disconnect()
    }
    
    // 使用TaskID建立新连接
    connect(taskId)
    
    // 等待连接建立
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('任务连接超时'))
      }, 10000)
      
      socket.value.on('connect', () => {
        clearTimeout(timeout)
        console.log('✅ 任务专用连接建立成功')
        console.log('🆔 连接ID:', socket.value.id)
        console.log('🎯 任务ID:', taskId)
        resolve(socket.value.id)
      })
      
      socket.value.on('connect_error', (error) => {
        clearTimeout(timeout)
        console.error('❌ 任务连接失败:', error)
        reject(error)
      })
    })
  }

  // 🔧 新增：任务完成后断开连接
  const disconnectTask = (taskId) => {
    console.log('🏁 任务完成，断开专用连接:', taskId)
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
      isConnected.value = false
    }
    
    // 重新建立通用连接（用于聊天等其他功能）
    setTimeout(() => {
      console.log('🔄 重新建立通用WebSocket连接')
      connect()
    }, 1000)
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
      // 聊天始终使用HTTP API，保持原有行为
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
      console.log('📁 开始文件上传流程')
      console.log('🔍 上传开始时的WebSocket状态:')
      console.log('  连接状态:', isConnected.value)
      console.log('  Session ID:', socket.value?.id || 'N/A')
      console.log('  前端ID:', clientId.value)
      console.log('⏰ 上传开始时间:', new Date().toLocaleTimeString())
      
      parsingStatus.value = 'uploading'
      parsingProgress.value = 0
      
      // 检查文件大小（21MB限制）
      const maxFileSize = 21 * 1024 * 1024 // 21MB
      const actualFileSize = file.size || (file.raw && file.raw.size) || 0
      if (actualFileSize > maxFileSize) {
        throw new Error(`文件大小 ${(actualFileSize / (1024 * 1024)).toFixed(1)}MB 超过限制，最大允许 21MB`)
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
      
      // 安全地获取文件对象并转换为base64
      let actualFile = null
      if (file.raw && file.raw instanceof File) {
        // Element Plus 文件对象格式
        actualFile = file.raw
      } else if (file instanceof File) {
        // 原生 File 对象
        actualFile = file
      } else {
        throw new Error('无效的文件格式: 无法识别的文件对象')
      }
      
      console.log('🔥 [上传] 文件对象类型检查:', {
        hasRaw: !!file.raw,
        rawIsFile: file.raw instanceof File,
        fileIsFile: file instanceof File,
        actualFileType: actualFile?.constructor?.name,
        fileName: file.name || actualFile?.name
      })
      
      const fileContent = await fileToBase64(actualFile)
      
      const fileInfo = {
        name: file.name || actualFile.name,
        type: actualFile.type,
        size: file.size || actualFile.size,
        content: fileContent
      }

      // 调用后端文件上传API
      console.log('🌐 准备调用文件上传API')
      console.log('  上传前Session ID:', socket.value?.id || 'N/A')
      console.log('⏰ API调用开始时间:', new Date().toLocaleTimeString())
      
      const response = await api.post('/api/file/upload', {
        file_info: fileInfo,
        client_id: clientId.value
      })
      
      console.log('✅ 文件上传API调用完成')
      console.log('  上传后Session ID:', socket.value?.id || 'N/A')
      console.log('  连接状态:', isConnected.value)
      console.log('⏰ API调用完成时间:', new Date().toLocaleTimeString())

      if (response.data.success) {
        const taskId = response.data.task_id
        
        // 🔧 简化方案：立即建立强绑定映射
        console.log('🎯 [简化方案] 立即建立TaskID映射')
        console.log('  TaskID:', taskId)
        console.log('  当前SessionID:', socket.value?.id)
        
        // 确保WebSocket连接存在
        if (!socket.value || !isConnected.value) {
          console.log('🔄 WebSocket未连接，重新建立连接...')
          connect()
          
          // 等待连接建立
          await new Promise((resolve, reject) => {
            const checkConnection = () => {
              if (isConnected.value && socket.value) {
                resolve()
              } else {
                setTimeout(checkConnection, 100)
              }
            }
            setTimeout(() => reject(new Error('连接超时')), 5000)
            checkConnection()
          })
        }
        
        // 立即发送强绑定映射
        const strongBindingMessage = {
          task_id: taskId,
          session_id: socket.value.id,
          action: 'strong_binding',
          client_type: 'frontend',
          timestamp: Date.now()
        }
        
        console.log('📡 [简化方案] 发送强绑定映射:', strongBindingMessage)
        socket.value.emit('establish_task_binding', strongBindingMessage)
        
        // 等待绑定确认
        await new Promise(resolve => setTimeout(resolve, 300))
        
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
          fileName: file.name || actualFile.name,
          fileType: actualFile.type,
          fileSize: file.size || actualFile.size,
          filePath: response.data.file_path,
          status: 'pending',
          progress: 0,
          steps: [],
          result: null,
          contentAnalysis: null,
          aiAnalysis: null,
          error: null,
          createdAt: new Date(),
          updatedAt: new Date(),
          // 🔧 新增：记录初始SessionID
          initialSessionId: socket.value?.id,
          currentSessionId: socket.value?.id
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
        
        // 通过Socket.IO通知后端开始分析
        if (socket.value && isConnected.value) {
          // 🔧 增强：检查连接稳定性和Session一致性
          console.log('🔍 [Session映射] 检查WebSocket连接状态...')
          console.log('🔌 连接状态:', isConnected.value)
          console.log('🆔 当前Session ID:', socket.value.id)
          console.log('🆔 任务记录的Session ID:', task.currentSessionId)
          
          // 如果SessionID发生变化，更新映射
          if (socket.value.id !== task.currentSessionId) {
            console.log('⚠️ [Session映射] 检测到SessionID变化，更新映射...')
            console.log('  旧SessionID:', task.currentSessionId)
            console.log('  新SessionID:', socket.value.id)
            
            // 更新任务记录
            task.currentSessionId = socket.value.id
            parsingTasks.value.set(taskId, task)
            
            // 发送Session映射更新
            const sessionUpdateMessage = {
              task_id: taskId,
              new_session_id: socket.value.id,
              old_session_id: task.initialSessionId,
              client_type: 'frontend',
              action: 'session_changed'
            }
            
            console.log('📡 [Session映射] 发送Session变更通知:', sessionUpdateMessage)
            socket.value.emit('update_session_mapping', sessionUpdateMessage)
            
            // 等待映射更新完成
            await new Promise(resolve => setTimeout(resolve, 800))
          }
          
          // 发送开始分析请求
          const analysisMessage = {
            task_id: taskId,
            execution_mode: 'automatic',
            socket_session_id: socket.value.id,  // 使用Socket.IO的session ID
            client_id: clientId.value,
            session_id: sessionId.value
          }
          
          console.log('🆔 [Session映射] 最终分析请求:', analysisMessage)
          console.log('🔄 发送的socket_session_id:', socket.value.id)
          
          socket.value.emit('start_analysis', analysisMessage)
          
          console.log('📡 ✅ start_analysis事件已发送')
          console.log('⏰ 发送时间:', new Date().toLocaleTimeString())
          
          return { success: true, task_id: taskId }
        } else {
          throw new Error('WebSocket连接不可用')
        }
      } else {
        throw new Error('文件上传失败: ' + (response.data.error || '未知错误'))
      }
      
    } catch (error) {
      console.error('🔥 [WebSocket] 文件上传失败:', error)
      parsingStatus.value = 'failed'
      
      // 添加失败步骤
      updateProcessingStep({
        id: 'step_upload',
        title: '文档上传',
        description: `上传失败: ${error.message}`,
        status: 'danger',
        progress: 0,
        timestamp: new Date().toLocaleTimeString()
      })
      
      throw error
    }
  }

  // 注意：专注于WebSocket实时通信，不再使用HTTP轮询备用方案

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

      const response = await api.post(`/api/file/analyze/${taskId}`)
      
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
          console.log(`🤖 AI分析状态: ${task.status}, 进度: ${task.progress || 0}%`)
          
          const localTask = parsingTasks.value.get(taskId)
          
          if (localTask) {
            localTask.status = task.status
            localTask.result = task.parsing_result
            localTask.contentAnalysis = task.content_analysis
            localTask.aiAnalysis = task.ai_analysis
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
          
          // 严格检查：只有当状态为 'fully_completed' 时才完成
          if (task.status === 'fully_completed') {
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
              currentParsingTask.value.result = task.parsing_result
              currentParsingTask.value.contentAnalysis = task.content_analysis
              currentParsingTask.value.aiAnalysis = task.ai_analysis
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
            if (task.parsing_result) {
              setAnalysisResult({
                title: `${task.parsing_result.file_name} - 完整分析结果`,
                type: task.parsing_result.type,
                timestamp: Date.now(),
                fileInfo: {
                  name: task.parsing_result.file_name,
                  type: task.parsing_result.file_type,
                  size: task.parsing_result.file_size
                },
                content: task.parsing_result.text_content || task.parsing_result.content,
                details: task.parsing_result,
                contentAnalysis: task.content_analysis,
                aiAnalysis: task.ai_analysis,
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
          
          if (task.status === 'ai_failed') {
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

  // 分析文档方法 - 统一入口
  const analyzeDocument = async (file) => {
    console.log('🔥 [WebSocketStore] 开始分析文档:', file.name)
    try {
      // 使用现有的uploadFile方法
      await uploadFile(file)
      
      // 添加处理步骤
      addProcessingStep({
        id: generateMessageId(),
        title: '文档分析',
        description: `正在分析文档: ${file.name}`,
        status: 'primary',
        progress: 0,
        timestamp: new Date().toLocaleTimeString()
      })
      
      return true
    } catch (error) {
      console.error('🔥 [WebSocketStore] 文档分析失败:', error)
      throw error
    }
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

  // 🔧 新增：Session一致性监控
  let sessionConsistencyTimer = null
  
  const startSessionConsistencyMonitoring = () => {
    // 清除之前的定时器
    if (sessionConsistencyTimer) {
      clearInterval(sessionConsistencyTimer)
    }
    
    // 每5秒检查一次Session一致性
    sessionConsistencyTimer = setInterval(() => {
      if (!socket.value || !isConnected.value) {
        return
      }
      
      console.log('🔍 [Session监控] 开始Session一致性检查...')
      
      // 检查当前进行中的任务
      let needSync = false
      for (const [taskId, task] of parsingTasks.value.entries()) {
        if (task.status !== 'completed' && task.status !== 'failed') {
          if (task.currentSessionId !== socket.value.id) {
            console.log(`⚠️ [Session监控] 发现Session不一致: Task[${taskId}]`)
            console.log(`  记录的SessionID: ${task.currentSessionId}`)
            console.log(`  当前SessionID: ${socket.value.id}`)
            needSync = true
            
            // 更新任务记录
            task.currentSessionId = socket.value.id
            parsingTasks.value.set(taskId, task)
            
            // 发送同步请求
            const syncMessage = {
              task_id: taskId,
              new_session_id: socket.value.id,
              old_session_id: task.initialSessionId,
              client_type: 'frontend',
              action: 'consistency_check'
            }
            
            console.log(`📡 [Session监控] 发送一致性修复:`, syncMessage)
            socket.value.emit('update_session_mapping', syncMessage)
          }
        }
      }
      
      if (!needSync) {
        console.log('✅ [Session监控] Session映射一致性检查通过')
      }
    }, 5000) // 5秒检查一次
  }
  
  const stopSessionConsistencyMonitoring = () => {
    if (sessionConsistencyTimer) {
      clearInterval(sessionConsistencyTimer)
      sessionConsistencyTimer = null
      console.log('🛑 [Session监控] 停止Session一致性监控')
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
    
    // 处理步骤
    processingSteps,
    currentProcessing,
    analysisResult,
    
    // 轮询管理
    activePolls,
    
    // 计算属性
    lastMessage,
    isFileProcessing,
    
    // 方法
    connect,
    disconnect,
    connectForTask,
    disconnectTask,
    sendMessage,
    addMessage,
    clearMessages,
    addProcessingStep,
    updateProcessingStep,
    clearProcessingSteps,
    setCurrentProcessing,
    setAnalysisResult,
    clearAnalysisResult,
    analyzeDocument,
    checkHealth,
    getSessions,
    uploadFile,
    getParsingStatus,
    fileToBase64,
    resetParsingState,
    clearAllPolling,
    startContentAnalysis,
    startAIAnalysis,
    getUploadedFiles,
    deleteUploadedFile,
    updateSessionId,
    // 导出工具函数
    generateMessageId: () => generateMessageId(),
    generateClientId: () => generateClientId(),
    generateSessionId: () => generateSessionId(),
    // 导出Markdown生成函数
    generateMarkdownReport,
    // 🔧 新增：Session一致性监控
    startSessionConsistencyMonitoring,
    stopSessionConsistencyMonitoring,
    // 🔧 调试：导出handleAnalysisProgress函数
    handleAnalysisProgress
  }
}) 