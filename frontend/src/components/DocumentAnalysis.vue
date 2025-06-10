<template>
  <div class="document-analysis">
    <!-- 头部区域 -->
    <div class="header">
      <h1>智能文档分析系统</h1>
      <p class="subtitle">支持多阶段分析流程 · WebSocket实时通信</p>
    </div>

    <!-- 主要内容区域 -->
    <el-tabs v-model="activeTab" class="analysis-tabs">
      <!-- 分析进度标签页 -->
      <el-tab-pane label="分析进度" name="progress">
        <!-- 文件上传区域 -->
        <div class="upload-section" v-if="!taskId">
          <el-upload
            drag
            :show-file-list="false"
            :before-upload="handleFileUpload"
            accept=".txt,.doc,.docx,.pdf"
            class="upload-area"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖拽到此处，或<em>点击上传</em>
            </div>
            <div class="el-upload__tip">
              支持 txt、doc、docx、pdf 格式文件
            </div>
          </el-upload>
        </div>

        <!-- 分析进度区域 -->
        <div class="analysis-section" v-if="taskId">
          <div class="task-info">
            <h3>任务 ID: {{ taskId }}</h3>
            <p>文件: {{ fileName }}</p>
            <p>模式: WebSocket 实时通信</p>
          </div>

          <!-- 三个分析阶段 -->
          <div class="stages-container">
            <!-- 文档解析阶段 -->
            <div class="stage-card">
              <div class="stage-header">
                <h4>文档解析</h4>
                <span>{{ stageProgress.document_parsing }}%</span>
              </div>
              <el-progress
                :percentage="stageProgress.document_parsing"
                :stroke-width="8"
              ></el-progress>
            </div>

            <!-- 内容分析阶段 -->
            <div class="stage-card">
              <div class="stage-header">
                <h4>内容分析</h4>
                <span>{{ stageProgress.content_analysis }}%</span>
              </div>
              <el-progress
                :percentage="stageProgress.content_analysis"
                :stroke-width="8"
              ></el-progress>
            </div>

            <!-- AI智能分析阶段 -->
            <div class="stage-card">
              <div class="stage-header">
                <h4>AI智能分析</h4>
                <span>{{ stageProgress.ai_analysis }}%</span>
              </div>
              <el-progress
                :percentage="stageProgress.ai_analysis"
                :stroke-width="8"
              ></el-progress>
            </div>
          </div>

          <!-- 控制按钮 -->
          <div class="control-buttons">
            <el-button @click="refreshProgress" :loading="refreshing">
              刷新进度
            </el-button>
            <el-button @click="resetTask" type="info">
              重新开始
            </el-button>
            <el-button 
              @click="generateReport" 
              :loading="reportLoading"
              :disabled="!isAnalysisCompleted"
              type="primary"
            >
              生成分析报告
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- 分析报告标签页 -->
      <el-tab-pane label="分析报告" name="report" :disabled="!hasReport">
        <div class="report-section">
          <div class="report-header">
            <h3>需求文档分析报告</h3>
            <div class="report-actions">
              <el-button @click="refreshReport" :loading="reportLoading" size="small">
                刷新报告
              </el-button>
              <el-button @click="downloadReport" size="small" type="primary">
                下载报告
              </el-button>
            </div>
          </div>
          
          <div class="report-content" v-if="markdownReport">
            <div v-html="renderedMarkdown" class="markdown-content"></div>
          </div>
          
          <div class="report-empty" v-else>
            <el-empty description="暂无报告内容">
              <el-button @click="generateReport" type="primary">生成报告</el-button>
            </el-empty>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'
import { io } from 'socket.io-client'
import MarkdownIt from 'markdown-it'

// 初始化markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

// 添加调试日志函数
const log = (message, data) => {
  console.log(`🔥 [DocumentAnalysis] ${message}`, data || '')
}

// 响应式数据
const activeTab = ref('progress')
const taskId = ref('')
const fileName = ref('')
const refreshing = ref(false)
const reportLoading = ref(false)
const markdownReport = ref('')
const hasReport = ref(false)
let progressMonitorTimer = null

// 阶段进度
const stageProgress = ref({
  document_parsing: 0,
  content_analysis: 0,
  ai_analysis: 0
})

// 通信相关
let socket = null

// API配置
const HTTP_API_BASE_URL = 'http://localhost:8082/api'
const WEBSOCKET_URL = 'http://localhost:8081'

// 计算属性
const isAnalysisCompleted = computed(() => {
  return stageProgress.value.document_parsing === 100 &&
         stageProgress.value.content_analysis === 100 &&
         stageProgress.value.ai_analysis === 100
})

const renderedMarkdown = computed(() => {
  if (!markdownReport.value) return ''
  return md.render(markdownReport.value)
})

// 监听分析完成状态
watch(isAnalysisCompleted, (newVal) => {
  if (newVal) {
    log('分析已完成，可以生成报告')
    // 停止进度监控
    if (progressMonitorTimer) {
      clearInterval(progressMonitorTimer)
      progressMonitorTimer = null
    }
    // 分析完成后自动生成报告
    setTimeout(() => {
      generateReport()
    }, 2000)
  }
})

// 启动进度监控定时器
const startProgressMonitor = () => {
  if (progressMonitorTimer) {
    clearInterval(progressMonitorTimer)
  }
  
  log('启动进度监控定时器')
  progressMonitorTimer = setInterval(() => {
    if (taskId.value && !isAnalysisCompleted.value) {
      log('定期检查进度状态')
      if (socket && socket.connected) {
        socket.emit('get_analysis_progress', { task_id: taskId.value })
      }
    }
  }, 10000) // 每10秒检查一次
}

// 停止进度监控定时器
const stopProgressMonitor = () => {
  if (progressMonitorTimer) {
    clearInterval(progressMonitorTimer)
    progressMonitorTimer = null
    log('已停止进度监控定时器')
  }
}

// 初始化WebSocket连接
const initializeWebSocket = async () => {
  try {
    log('初始化WebSocket连接')
    
    socket = io(WEBSOCKET_URL, {
      transports: ['websocket'],
      timeout: 5000
    })

    socket.on('connect', () => {
      log('WebSocket连接成功')
    })

    socket.on('disconnect', () => {
      log('WebSocket连接断开')
    })

    // 设置事件监听器
    socket.on('analysis_progress', (data) => {
      console.log('🔥 [WebSocket] 收到 analysis_progress 事件:', data)
      console.log('🔥 [WebSocket] 当前任务ID:', taskId.value)
      console.log('🔥 [WebSocket] 事件任务ID:', data.task_id)
      
      if (data.task_id === taskId.value) {
        console.log('🔥 [WebSocket] 任务ID匹配，开始更新进度')
        
        if (data.stage_progress) {
          console.log('🔥 [WebSocket] 接收到的阶段进度:', data.stage_progress)
          console.log('🔥 [WebSocket] 更新前的进度:', JSON.parse(JSON.stringify(stageProgress.value)))
          
          // 更新所有阶段的进度
          Object.keys(data.stage_progress).forEach(stage => {
            if (stageProgress.value.hasOwnProperty(stage)) {
              const oldValue = stageProgress.value[stage]
              stageProgress.value[stage] = data.stage_progress[stage]
              console.log(`🔥 [WebSocket] ${stage}: ${oldValue} -> ${data.stage_progress[stage]}`)
            }
          })
          
          console.log('🔥 [WebSocket] 更新后的进度:', JSON.parse(JSON.stringify(stageProgress.value)))
        } else {
          console.log('🔥 [WebSocket] 没有stage_progress数据')
        }
        
        // 强制触发界面更新
        nextTick(() => {
          console.log('🔥 [WebSocket] 强制更新完成，当前进度:', JSON.parse(JSON.stringify(stageProgress.value)))
        })
      } else {
        console.log('🔥 [WebSocket] 任务ID不匹配，忽略此事件')
      }
    })

    socket.on('stage_completed', (data) => {
      log('WebSocket 阶段完成', data)
      if (data.task_id === taskId.value) {
        if (data.stage && stageProgress.value.hasOwnProperty(data.stage)) {
          stageProgress.value[data.stage] = 100
        }
        ElMessage.success(`${getStageName(data.stage)} 阶段已完成`)
      }
    })

    socket.on('analysis_completed', (data) => {
      log('WebSocket 分析完成', data)
      if (data.task_id === taskId.value) {
        Object.keys(stageProgress.value).forEach(stage => {
          stageProgress.value[stage] = 100
        })
        ElMessage.success('完整分析已完成！')
      }
    })

    // 监听任务绑定确认
    socket.on('task_binding_confirmed', (data) => {
      log('WebSocket 任务绑定确认', data)
      if (data.task_id === taskId.value) {
        ElMessage.success('任务绑定成功，正在接收进度更新')
        // 绑定成功后立即请求一次进度状态
        setTimeout(() => {
          socket.emit('get_analysis_progress', { task_id: taskId.value })
          log('绑定成功后请求进度状态')
        }, 500)
      }
    })

    // 监听任务绑定错误
    socket.on('task_binding_error', (data) => {
      log('WebSocket 任务绑定错误', data)
      ElMessage.error('任务绑定失败: ' + data.error)
      // 绑定失败时重试
      if (taskId.value) {
        setTimeout(() => {
          log('重试任务绑定', taskId.value)
          socket.emit('establish_task_binding', {
            task_id: taskId.value,
            session_id: socket.id,
            action: 'retry_binding'
          })
        }, 3000)
      }
    })

    // 监听所有WebSocket事件用于调试
    socket.onAny((eventName, ...args) => {
      log(`收到WebSocket事件: ${eventName}`, args)
    })

  } catch (error) {
    log('WebSocket连接失败', error)
  }
}

// 获取阶段中文名称
const getStageName = (stage) => {
  const stageNames = {
    'document_parsing': '文档解析',
    'content_analysis': '内容分析',
    'ai_analysis': 'AI智能分析'
  }
  return stageNames[stage] || stage
}

// 文件上传处理
const handleFileUpload = async (file) => {
  try {
    log('开始文件上传', file.name)
    
    // 重置状态
    taskId.value = ''
    fileName.value = ''
    markdownReport.value = ''
    hasReport.value = false
    activeTab.value = 'progress'
    Object.keys(stageProgress.value).forEach(stage => {
      stageProgress.value[stage] = 0
    })
    
    // 创建FormData
    const formData = new FormData()
    formData.append('file', file)
    formData.append('execution_mode', 'automatic')
    
    log('发送上传请求')
    
    const response = await axios.post(`${HTTP_API_BASE_URL}/file/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    log('服务器响应', response.data)
    
    if (response.data.success) {
      taskId.value = response.data.task_id
      fileName.value = file.name
      
      ElMessage.success('分析任务已开始，正在监听WebSocket进度更新...')
      
      // 立即建立任务绑定
      if (socket && socket.connected) {
        log('立即建立任务绑定', taskId.value)
        socket.emit('establish_task_binding', {
          task_id: taskId.value,
          session_id: socket.id,
          action: 'strong_binding'
        })
        
        // 延迟请求初始进度状态
        setTimeout(() => {
          socket.emit('get_analysis_progress', { task_id: taskId.value })
          log('请求初始进度状态')
        }, 2000)
        
        // 启动进度监控
        startProgressMonitor()
      }
    } else {
      log('分析启动失败', response.data)
      ElMessage.error(response.data.error || '启动分析失败')
    }
  } catch (error) {
    log('上传失败', error)
    ElMessage.error('文件上传失败: ' + error.message)
  }
  
  return false // 阻止自动上传
}

// 刷新进度
const refreshProgress = async () => {
  if (!taskId.value) return
  
  try {
    refreshing.value = true
    log('手动刷新进度')
    
    const response = await axios.get(`${HTTP_API_BASE_URL}/v2/analysis/progress/${taskId.value}`)
    log('进度查询响应', response.data)
    
    if (response.data.success && response.data.data.progress) {
      const progress = response.data.data.progress
      Object.keys(progress).forEach(stage => {
        if (stageProgress.value.hasOwnProperty(stage)) {
          stageProgress.value[stage] = progress[stage]
        }
      })
      ElMessage.success('进度已刷新')
    }
  } catch (error) {
    log('刷新进度失败', error)
    ElMessage.error('刷新进度失败')
  } finally {
    refreshing.value = false
  }
}

// 生成分析报告
const generateReport = async () => {
  if (!taskId.value) {
    ElMessage.warning('请先上传文件并完成分析')
    return
  }
  
  try {
    reportLoading.value = true
    log('开始生成分析报告')
    
    const response = await axios.get(`${HTTP_API_BASE_URL}/v2/analysis/markdown/${taskId.value}`)
    log('报告生成响应', response.data)
    
    if (response.data.success) {
      markdownReport.value = response.data.markdown
      hasReport.value = true
      activeTab.value = 'report'
      ElMessage.success('分析报告已生成')
    } else {
      ElMessage.error(response.data.error || '生成报告失败')
    }
  } catch (error) {
    log('生成报告失败', error)
    if (error.response && error.response.status === 404) {
      ElMessage.error('分析结果不存在，请确保分析已完成')
    } else {
      ElMessage.error('生成报告失败: ' + error.message)
    }
  } finally {
    reportLoading.value = false
  }
}

// 刷新报告
const refreshReport = async () => {
  await generateReport()
}

// 下载报告
const downloadReport = () => {
  if (!markdownReport.value) {
    ElMessage.warning('暂无报告内容')
    return
  }
  
  try {
    const blob = new Blob([markdownReport.value], { type: 'text/markdown' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `analysis_report_${taskId.value}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('报告下载成功')
  } catch (error) {
    log('下载报告失败', error)
    ElMessage.error('下载失败')
  }
}

// 重新开始
const resetTask = () => {
  // 停止进度监控
  stopProgressMonitor()
  
  taskId.value = ''
  fileName.value = ''
  markdownReport.value = ''
  hasReport.value = false
  activeTab.value = 'progress'
  Object.keys(stageProgress.value).forEach(stage => {
    stageProgress.value[stage] = 0
  })
  ElMessage.success('已重置')
}

// 生命周期
onMounted(() => {
  initializeWebSocket()
})

onUnmounted(() => {
  // 清理定时器
  stopProgressMonitor()
  
  // 断开WebSocket连接
  if (socket) {
    socket.disconnect()
  }
})
</script>

<style lang="scss" scoped>
.document-analysis {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  
  .header {
    text-align: center;
    margin-bottom: 30px;
    
    h1 {
      color: #2c3e50;
      margin-bottom: 8px;
    }
    
    .subtitle {
      color: #7f8c8d;
      font-size: 16px;
    }
  }
  
  .analysis-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 20px;
    }
    
    :deep(.el-tabs__content) {
      min-height: 500px;
    }
  }
  
  .upload-section {
    margin-bottom: 40px;
    
    .upload-area {
      margin-bottom: 20px;
      
      :deep(.el-upload) {
        width: 100%;
      }
      
      :deep(.el-upload-dragger) {
        width: 100%;
        height: 200px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }
    }
  }
  
  .analysis-section {
    .task-info {
      background: #f8f9fa;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 30px;
      
      h3 {
        margin: 0 0 10px 0;
        color: #2c3e50;
      }
      
      p {
        margin: 5px 0;
        color: #666;
      }
    }
    
    .stages-container {
      display: grid;
      gap: 20px;
      margin-bottom: 30px;
      
      .stage-card {
        border: 2px solid #e1e8ed;
        border-radius: 12px;
        padding: 20px;
        background: white;
        
        .stage-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
          
          h4 {
            margin: 0;
            color: #2c3e50;
          }
        }
      }
    }
    
    .control-buttons {
      display: flex;
      justify-content: center;
      gap: 15px;
    }
  }
  
  .report-section {
    .report-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 15px;
      border-bottom: 1px solid #e1e8ed;
      
      h3 {
        margin: 0;
        color: #2c3e50;
      }
      
      .report-actions {
        display: flex;
        gap: 10px;
      }
    }
    
    .report-content {
      background: white;
      border: 1px solid #e1e8ed;
      border-radius: 8px;
      padding: 30px;
      max-height: 70vh;
      overflow-y: auto;
      
      .markdown-content {
        :deep(h1) {
          color: #2c3e50;
          border-bottom: 2px solid #3498db;
          padding-bottom: 10px;
          margin-bottom: 20px;
        }
        
        :deep(h2) {
          color: #34495e;
          margin-top: 30px;
          margin-bottom: 15px;
          border-left: 4px solid #3498db;
          padding-left: 15px;
        }
        
        :deep(h3) {
          color: #2c3e50;
          margin-top: 25px;
          margin-bottom: 12px;
        }
        
        :deep(h4) {
          color: #34495e;
          margin-top: 20px;
          margin-bottom: 10px;
        }
        
        :deep(blockquote) {
          background: #f8f9fa;
          border-left: 4px solid #3498db;
          padding: 15px 20px;
          margin: 15px 0;
          border-radius: 4px;
        }
        
        :deep(ul, ol) {
          margin: 10px 0;
          padding-left: 20px;
        }
        
        :deep(li) {
          margin: 5px 0;
          line-height: 1.6;
        }
        
        :deep(p) {
          line-height: 1.6;
          margin: 10px 0;
        }
        
        :deep(code) {
          background: #f1f2f6;
          padding: 2px 6px;
          border-radius: 4px;
          font-family: Monaco, Consolas, monospace;
        }
        
        :deep(pre) {
          background: #f8f9fa;
          padding: 15px;
          border-radius: 6px;
          overflow-x: auto;
          border: 1px solid #e9ecef;
        }
        
        :deep(table) {
          width: 100%;
          border-collapse: collapse;
          margin: 15px 0;
          
          th, td {
            border: 1px solid #dee2e6;
            padding: 8px 12px;
            text-align: left;
          }
          
          th {
            background: #f8f9fa;
            font-weight: bold;
          }
        }
        
        :deep(hr) {
          border: none;
          border-top: 2px solid #e9ecef;
          margin: 30px 0;
        }
      }
    }
    
    .report-empty {
      text-align: center;
      padding: 60px 20px;
    }
  }
}
</style>