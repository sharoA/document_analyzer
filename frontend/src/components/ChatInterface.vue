<template>
  <div class="chat-container">
    <!-- 左侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2 class="app-title">
          <el-icon><ChatDotRound /></el-icon>
          analyDesign
        </h2>
        <el-button 
          type="primary" 
          @click="startNewChat"
          class="new-chat-btn"
        >
          新任务
        </el-button>
      </div>
      
      <div class="chat-history">
        <div class="history-section">
          <h3>需求文档智能分析</h3>
          <p class="section-subtitle">文档解析专家</p>
        </div>
        
        <div class="task-description">
          <h4>智能文档分析</h4>
          <p>支持 Word、PDF、TXT、Markdown 格式文档分析</p>
          
          <div class="feature-tips">
            <p>💡 点击下方"附件"按钮上传文档，点击上传文档后面开始分析按钮进行解析</p>
          </div>
        </div>
      </div>

      <!-- 聊天消息区域 -->
      <div class="chat-messages" ref="messagesContainer">
        <div 
          v-for="message in messages" 
          :key="message.message_id"
          :class="['message', message.type]"
        >
          <div v-if="message.type === 'user'" class="user-message">
            <div class="message-content">{{ message.message }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
          
          <div v-else-if="message.type === 'chat_response'" class="bot-message">
            <div class="bot-avatar">
              <el-icon><User /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(message.message)"></div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
        </div>
        
        <div v-if="isTyping" class="typing-indicator">
          <div class="bot-avatar">
            <el-icon><User /></el-icon>
          </div>
          <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <div class="input-container">
          <!-- 隐藏的文件上传组件 -->
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :show-file-list="false"
            accept=".doc,.docx,.pdf,.txt,.md"
            style="display: none;"
          />
          
          <!-- 显示已上传的文件 -->
          <div v-if="uploadedFile" class="uploaded-file-info">
            <div class="file-info-container">
              <el-icon class="file-icon"><Document /></el-icon>
              <div class="file-details">
                <div class="file-name">{{ uploadedFile.name }}</div>
                <div class="file-size">{{ formatFileSize(uploadedFile.size) }}</div>
              </div>
              <el-button 
                type="text" 
                size="small" 
                @click="removeFile"
                class="close-btn"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <el-button 
              type="primary" 
              size="small" 
              @click="analyzeDocument"
              :loading="isAnalyzing"
              class="analyze-btn"
            >
              开始分析
            </el-button>
          </div>
          
          <el-input
            v-model="currentMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题或需求..."
            @keydown.ctrl.enter="sendMessage"
            :disabled="isTyping"
            resize="none"
          />
          <div class="input-actions">
            <el-button-group>
              <el-button size="small" @click="attachFile">
                <el-icon><Paperclip /></el-icon>
                附件
              </el-button>
              <el-button size="small" @click="expandInput">
                <el-icon><FullScreen /></el-icon>
                展开
              </el-button>
            </el-button-group>
            <el-button 
              type="primary" 
              @click="sendMessage"
              :disabled="!currentMessage.trim() || isTyping"
              :loading="isTyping"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧 Agent 工作空间 -->
    <div class="agent-workspace">
      <!-- 工作空间头部 -->
      <div class="workspace-header">
        <h3>Agent 的工作空间</h3>
        <div class="connection-status">
          <el-tag 
            :type="connectionStatusType" 
            size="small"
            effect="plain"
          >
            <el-icon><Connection /></el-icon>
            {{ connectionStatusText }}
          </el-tag>
        </div>
      </div>

      <!-- Tab 导航 -->
      <el-tabs v-model="activeTab" class="workspace-tabs">
        <!-- 实时处理状态 -->
        <el-tab-pane label="实时跟随" name="realtime">
          <div class="tab-content">
            <div class="status-header">
              <h4>处理状态</h4>
              <el-tag :type="processingStatus.type" size="small">
                {{ processingStatus.text }}
              </el-tag>
            </div>
            
            <div class="processing-steps">
              <el-timeline>
                <el-timeline-item
                  v-for="step in processingSteps"
                  :key="step.id"
                  :type="step.status"
                  :timestamp="step.timestamp"
                >
                  <div class="step-content">
                    <h5>{{ step.title }}</h5>
                    <p>{{ step.description }}</p>
                    <div v-if="step.progress !== undefined" class="step-progress">
                      <el-progress 
                        :percentage="step.status === 'success' ? 100 : step.progress" 
                        :status="step.status === 'success' ? 'success' : undefined"
                      />
                    </div>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>
            
            <div v-if="currentProcessing" class="current-processing">
              <el-card>
                <template #header>
                  <div class="card-header">
                    <span>当前处理</span>
                    <el-icon class="rotating"><Loading /></el-icon>
                  </div>
                </template>
                <p>{{ currentProcessing.description }}</p>
                <el-progress 
                  :percentage="currentProcessing.progress || 0" 
                  :stroke-width="8"
                />
              </el-card>
            </div>
          </div>
        </el-tab-pane>

        <!-- 上传文档预览 -->
        <el-tab-pane label="上传文档预览" name="preview">
          <div class="tab-content">
            <div v-if="!uploadedFile" class="empty-state">
              <el-empty description="暂无上传文档">
                <el-button type="primary" @click="attachFile">
                  <el-icon><Paperclip /></el-icon>
                  上传文档
                </el-button>
              </el-empty>
            </div>
            
            <div v-else class="document-preview">
              <div class="preview-header">
                <h4>{{ getPreviewTitle(uploadedFile) }}</h4>
                <div class="file-info">
                  <el-tag size="small" type="success">
                    <el-icon><Document /></el-icon>
                    {{ uploadedFile.name }}
                  </el-tag>
                  <span class="file-size">{{ formatFileSize(uploadedFile.size) }}</span>
                </div>
              </div>
              
              <div class="preview-content">
                <!-- 文档基本信息 -->
                <el-card style="margin-bottom: 16px;">
                  <template #header>
                    <div style="display: flex; align-items: center;">
                      <el-icon style="margin-right: 8px;"><Document /></el-icon>
                      <span>文档信息</span>
                    </div>
                  </template>
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="文件名">
                      {{ uploadedFile.name }}
                    </el-descriptions-item>
                    <el-descriptions-item label="文件大小">
                      {{ formatFileSize(uploadedFile.size) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="文件类型">
                      {{ getFileType(uploadedFile) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="扩展名">
                      {{ getFileExtension(uploadedFile.name) }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-card>
                
                <!-- 文档预览区域 -->
                <el-card>
                  <template #header>
                    <div style="display: flex; align-items: center;">
                      <el-icon style="margin-right: 8px;"><Document /></el-icon>
                      <span>文档预览</span>
                    </div>
                  </template>
                  
                  <!-- 使用DocumentPreview组件 -->
                  <DocumentPreview :file="uploadedFile" />
                </el-card>
                
                <!-- 操作按钮 -->
                <div style="margin-top: 24px; text-align: center; padding: 20px; border-top: 1px solid #e4e7ed;">
                  <el-button type="primary" size="large" @click="analyzeDocument" :loading="isAnalyzing">
                    <el-icon><Promotion /></el-icon>
                    开始分析文档
                  </el-button>
                  <el-button size="large" @click="removeFile">
                    <el-icon><Close /></el-icon>
                    移除文档
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 需求文档分析 -->
        <el-tab-pane label="需求文档分析" name="analysis">
          <div class="tab-content">
            <div v-if="!analysisResult" class="empty-state">
              <div class="empty-content">
                <el-icon size="48" color="#c0c4cc"><Document /></el-icon>
                <h4>暂无分析结果</h4>
                <p>请上传文档进行分析</p>
              </div>
            </div>
            
            <div v-else class="analysis-content">
              <el-scrollbar height="100%">
                <div class="analysis-result">
                  <!-- 基本信息 -->
                  <el-card class="info-card">
                    <template #header>
                      <h5>基本信息</h5>
                    </template>
                    <div class="basic-info">
                      <div class="info-grid">
                        <el-table 
                          :data="basicInfoTable" 
                          :show-header="false"
                          border
                          style="width: 100%"
                        >
                          <el-table-column prop="label" width="120" />
                          <el-table-column prop="value" />
                        </el-table>
                      </div>
                    </div>
                  </el-card>
                  
                  <!-- 操作按钮 -->
                  <div class="result-actions">
                    <el-button type="primary" @click="analyzeWithAI">
                      <el-icon><Promotion /></el-icon>
                      智能处理
                    </el-button>
                    <el-button @click="exportResult">
                      <el-icon><Download /></el-icon>
                      导出结果
                    </el-button>
                    <el-button @click="clearResult">
                      <el-icon><Delete /></el-icon>
                      清空结果
                    </el-button>
                  </div>
                </div>
              </el-scrollbar>
            </div>
          </div>
        </el-tab-pane>

        <!-- 导出功能 -->
        <el-tab-pane label="导出功能" name="export">
          <div class="tab-content">
            <div class="export-options">
              <h4>导出选项</h4>
              
              <el-card class="export-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><Document /></el-icon>
                    <span>分析报告</span>
                  </div>
                </template>
                <p>导出完整的需求分析报告，包含所有分析结果和建议</p>
                <div class="export-actions">
                  <el-button-group>
                    <el-button @click="exportReport('pdf')" :disabled="!analysisResult">
                      <el-icon><Download /></el-icon>
                      PDF
                    </el-button>
                    <el-button @click="exportReport('word')" :disabled="!analysisResult">
                      <el-icon><Download /></el-icon>
                      Word
                    </el-button>
                    <el-button @click="exportReport('markdown')" :disabled="!analysisResult">
                      <el-icon><Download /></el-icon>
                      Markdown
                    </el-button>
                  </el-button-group>
                </div>
              </el-card>
              
              <el-card class="export-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><ChatDotRound /></el-icon>
                    <span>对话记录</span>
                  </div>
                </template>
                <p>导出完整的对话记录和交互历史</p>
                <div class="export-actions">
                  <el-button @click="exportChat()" :disabled="messages.length === 0">
                    <el-icon><Download /></el-icon>
                    导出对话
                  </el-button>
                </div>
              </el-card>
              
              <el-card class="export-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><Setting /></el-icon>
                    <span>自定义导出</span>
                  </div>
                </template>
                <p>选择特定内容进行导出</p>
                <div class="custom-export">
                  <el-checkbox-group v-model="exportOptions">
                    <el-checkbox value="basicInfo">基本信息</el-checkbox>
                    <el-checkbox value="clientInfo">需求方信息</el-checkbox>
                    <el-checkbox value="analysis">详细分析</el-checkbox>
                    <el-checkbox value="suggestions">建议和改进</el-checkbox>
                    <el-checkbox value="chat">对话记录</el-checkbox>
                  </el-checkbox-group>
                  <el-button 
                    type="primary" 
                    @click="exportCustom()" 
                    :disabled="exportOptions.length === 0"
                    style="margin-top: 10px;"
                  >
                    <el-icon><Download /></el-icon>
                    自定义导出
                  </el-button>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 隐藏的文件上传组件 -->
    <el-upload
      ref="uploadRef"
      :show-file-list="false"
      :before-upload="handleFileUpload"
      accept=".txt,.doc,.docx,.pdf"
      style="display: none;"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useWebSocketStore } from '../stores/websocket'
import { 
  ChatDotRound, 
  User, 
  Connection, 
  Document, 
  Loading, 
  Promotion,
  Close,
  Paperclip,
  FullScreen,
  Setting,
  Download,
  Delete
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DocumentPreview from './DocumentPreview.vue'

// 响应式数据
const currentMessage = ref('')
const messagesContainer = ref(null)
const uploadRef = ref(null)
const uploadedFile = ref(null)
const isAnalyzing = ref(false)
const isTyping = ref(false)
const isSending = ref(false)
const showRightPanel = ref(false)
const activeTab = ref('realtime')
const exportOptions = ref([])



// WebSocket store
const wsStore = useWebSocketStore()

// 调试：将store暴露到全局作用域
if (typeof window !== 'undefined') {
  window.wsStore = wsStore
  window.debugChatInterface = {
    wsStore,
    processingSteps: () => processingSteps.value,
    currentProcessing: () => currentProcessing.value,
    processingStatus: () => processingStatus.value
  }
  console.log('🔧 [调试] ChatInterface store已暴露到window.wsStore')
}

// 计算属性
const messages = computed(() => wsStore.messages || [])
const isConnected = computed(() => wsStore.isConnected)
const connectionStatus = computed(() => wsStore.connectionStatus)
const processingStatus = computed(() => ({
  type: wsStore.isProcessing ? 'warning' : 'success',
  text: wsStore.isProcessing ? '处理中...' : '就绪'
}))
const processingSteps = computed(() => wsStore.processingSteps || [])
const currentProcessing = computed(() => wsStore.currentProcessing)
const analysisResult = computed(() => wsStore.analysisResult)

const connectionStatusType = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return 'success'
    case 'connecting': return 'warning'
    case 'disconnected': return 'danger'
    default: return 'info'
  }
})

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return '已连接'
    case 'connecting': return '连接中'
    case 'disconnected': return '已断开'
    default: return '未知状态'
  }
})

const basicInfoTable = computed(() => {
  if (!analysisResult.value) return []
  
  return [
    { label: '文档名称', value: analysisResult.value.fileName || '未知' },
    { label: '文档类型', value: analysisResult.value.fileType || '未知' },
    { label: '文档大小', value: analysisResult.value.fileSize || '未知' },
    { label: '分析时间', value: analysisResult.value.analysisTime || '未知' },
    { label: '分析状态', value: analysisResult.value.status || '未知' }
  ]
})

const parsingStatusType = computed(() => {
  switch (wsStore.parsingStatus) {
    case 'uploading': return 'warning'
    case 'parsing': return 'primary'
    case 'content_analyzing': return 'primary'
    case 'ai_analyzing': return 'primary'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    default: return 'info'
  }
})

const parsingStatusText = computed(() => {
  switch (wsStore.parsingStatus) {
    case 'idle': return '待解析'
    case 'uploading': return '上传中'
    case 'parsing': return '文档解析中'
    case 'content_analyzing': return '内容分析中'
    case 'ai_analyzing': return '智能处理中'
    case 'completed': return '解析完成'
    case 'failed': return '解析失败'
    default: return '未知状态'
  }
})

// 方法
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatTime = (timestamp) => {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } catch (error) {
    return ''
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getFileType = (file) => {
  const typeMap = {
    'application/msword': 'Microsoft Word 文档',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Microsoft Word 文档',
    'application/pdf': 'PDF 文档',
    'text/plain': '纯文本文档',
    'text/markdown': 'Markdown 文档'
  }
  const fileType = file?.raw?.type || file?.type || 'unknown'
  return typeMap[fileType] || '未知文档类型'
}

const getFileExtension = (fileName) => {
  const lastDot = fileName.lastIndexOf('.')
  return lastDot !== -1 ? fileName.substring(lastDot) : '无扩展名'
}

const getPreviewTitle = (file) => {
  return '文档预览'
}

const formatMessage = (message) => {
  return message
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isTyping.value) return
  
  const message = currentMessage.value.trim()
  currentMessage.value = ''
  isTyping.value = true
  
  try {
    await wsStore.sendMessage(message)
  } catch (error) {
    ElMessage.error('发送消息失败: ' + error.message)
  } finally {
    isTyping.value = false
  }
}

const startNewChat = () => {
  wsStore.clearMessages()
  uploadedFile.value = null
  activeTab.value = 'realtime'
  ElMessage.success('已开始新任务')
}

const toggleRealtime = () => {
  ElMessage.info('实时问答功能开发中...')
}

const showFiles = () => {
  activeTab.value = 'files'
}

const attachFile = () => {
  // 触发隐藏的文件上传组件
  const fileInput = uploadRef.value?.$el.querySelector('input[type="file"]')
  if (fileInput) {
    fileInput.click()
  }
}

const expandInput = () => {
  ElMessageBox.prompt('请输入详细内容', '展开输入', {
    inputType: 'textarea',
    inputValue: currentMessage.value,
    inputPlaceholder: '请输入您的问题或需求...'
  }).then(({ value }) => {
    currentMessage.value = value
  }).catch(() => {
    // 用户取消
  })
}

const handleFileUpload = (file) => {
  console.log('🔥 [ChatInterface] 文件上传:', file.name)
  uploadedFile.value = file
  activeTab.value = 'preview'
  ElMessage.success(`文件 ${file.name} 上传成功`)
  return false // 阻止自动上传
}

const removeFile = () => {
  uploadedFile.value = null
  wsStore.clearAnalysisResult()
  ElMessage.success('文档已移除')
}

// 文件上传相关方法
const handleFileChange = (file) => {
  console.log('文件上传开始:', file)
  
  const allowedTypes = [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/pdf',
    'text/plain',
    'text/markdown'
  ]
  
  const fileType = file?.raw?.type || file?.type || 'unknown'
  console.log('文件类型:', fileType)
  console.log('文件名:', file.name)
  console.log('文件大小:', file.size)
  
  // 检查文件类型
  if (!allowedTypes.includes(fileType) && !file.name.match(/\.(doc|docx|pdf|txt|md)$/i)) {
    ElMessage.error('不支持的文件格式，请上传 Word、PDF、TXT 或 Markdown 文件')
    return false
  }
  
  // 检查文件大小（21MB限制）
  const maxFileSize = 21 * 1024 * 1024 // 21MB
  if (file.size > maxFileSize) {
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1)
    ElMessage.error(`文件大小 ${fileSizeMB}MB 超过限制，最大允许 21MB`)
    return false
  }
  
  uploadedFile.value = file
  console.log('uploadedFile设置完成:', uploadedFile.value)
  
  // 使用nextTick确保DOM更新后再切换页签
  nextTick(() => {
    console.log('切换到预览页签...')
    activeTab.value = 'preview'
    console.log('当前活动页签:', activeTab.value)
    
    // 强制触发响应式更新
    setTimeout(() => {
      console.log('延迟检查 - 当前页签:', activeTab.value)
      console.log('延迟检查 - 上传文件:', uploadedFile.value?.name)
    }, 100)
  })
  
  const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1)
  ElMessage.success(`文件 ${file.name} (${fileSizeMB}MB) 已选择，点击"开始分析"进行处理`)
}

const analyzeDocument = async () => {
  if (!uploadedFile.value) {
    ElMessage.warning('请先上传文档')
    return
  }
  
  isAnalyzing.value = true
  activeTab.value = 'realtime'
  
  try {
    // 清空之前的处理步骤
    wsStore.clearProcessingSteps()
    wsStore.resetParsingState()
    
    // 添加文档上传完成步骤
    wsStore.updateProcessingStep({
      id: 'step_upload',
      title: '文档上传',
      description: `文件上传完成: ${uploadedFile.value.name}`,
      status: 'success',
      timestamp: new Date().toLocaleTimeString(),
      progress: 100
    })
    
    // 使用WebSocket store的文件上传功能
    const result = await wsStore.uploadFile(uploadedFile.value)
    
    if (result.success) {
      ElMessage.success('文档解析已开始，请查看实时进度')
      
      // 监听解析状态变化
      const checkStatus = () => {
        if (wsStore.parsingStatus === 'completed') {
          ElMessage.success('文档解析完成')
          activeTab.value = 'files'
          isAnalyzing.value = false
        } else if (wsStore.parsingStatus === 'failed') {
          ElMessage.error('文档解析失败')
          isAnalyzing.value = false
        } else if (wsStore.isFileProcessing) {
          // 继续监听
          setTimeout(checkStatus, 1000)
        } else {
          isAnalyzing.value = false
        }
      }
      
      checkStatus()
    } else {
      throw new Error('文件上传失败')
    }
    
  } catch (error) {
    ElMessage.error('文档分析失败: ' + error.message)
    isAnalyzing.value = false
    
    // 添加失败步骤
    wsStore.updateProcessingStep({
      id: 'step_parsing_failed',
      title: '解析失败',
      description: `解析失败: ${error.message}`,
      status: 'danger',
      timestamp: new Date().toLocaleTimeString(),
      progress: 0
    })
  }
}

// 导出功能
const exportReport = async (format) => {
  if (!analysisResult.value) {
    ElMessage.warning('暂无分析结果可导出')
    return
  }
  
  try {
    // 这里应该调用后端API进行导出
    ElMessage.success(`正在导出 ${format.toUpperCase()} 格式的分析报告...`)
    
    // 模拟导出过程
    setTimeout(() => {
      ElMessage.success('导出完成')
    }, 2000)
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

const exportChat = async () => {
  if (messages.value.length === 0) {
    ElMessage.warning('暂无对话记录可导出')
    return
  }
  
  try {
    const chatContent = messages.value.map(msg => {
      const time = formatTime(msg.timestamp)
      const sender = msg.type === 'user' ? '用户' : 'AI助手'
      return `[${time}] ${sender}: ${msg.message}`
    }).join('\n')
    
    const blob = new Blob([chatContent], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `对话记录_${new Date().toLocaleDateString()}.txt`
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('对话记录导出完成')
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

const exportCustom = async () => {
  if (exportOptions.value.length === 0) {
    ElMessage.warning('请选择要导出的内容')
    return
  }
  
  try {
    let content = '# 自定义导出报告\n\n'
    
    if (exportOptions.value.includes('basicInfo') && analysisResult.value?.basicInfo) {
      content += '## 基本信息\n'
      Object.entries(analysisResult.value.basicInfo).forEach(([key, value]) => {
        content += `- ${key}: ${value}\n`
      })
      content += '\n'
    }
    
    if (exportOptions.value.includes('clientInfo') && analysisResult.value?.clientInfo) {
      content += '## 需求方信息\n'
      Object.entries(analysisResult.value.clientInfo).forEach(([key, value]) => {
        content += `- ${key}: ${value}\n`
      })
      content += '\n'
    }
    
    if (exportOptions.value.includes('analysis') && analysisResult.value?.analysis) {
      content += '## 详细分析\n'
      content += analysisResult.value.analysis.replace(/<[^>]*>/g, '') + '\n\n'
    }
    
    if (exportOptions.value.includes('suggestions') && analysisResult.value?.suggestions) {
      content += '## 建议和改进\n'
      analysisResult.value.suggestions.forEach(suggestion => {
        content += `- ${suggestion}\n`
      })
      content += '\n'
    }
    
    if (exportOptions.value.includes('chat') && messages.value.length > 0) {
      content += '## 对话记录\n'
      messages.value.forEach(msg => {
        const time = formatTime(msg.timestamp)
        const sender = msg.type === 'user' ? '用户' : 'AI助手'
        content += `**[${time}] ${sender}**: ${msg.message}\n\n`
      })
    }
    
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `自定义报告_${new Date().toLocaleDateString()}.md`
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('自定义导出完成')
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

// ================== 智能分析相关方法 ==================

// API配置
const HTTP_API_BASE_URL = 'http://localhost:8082/api/v2'
const WEBSOCKET_URL = 'http://localhost:8081'

// 智能分析通信相关
let smartSocket = null
let smartProgressTimer = null

// 智能分析计算属性
const isSmartAllCompleted = computed(() => {
  return Object.values(smartStageProgress.value).every(progress => progress === 100)
})

// 初始化智能分析连接
const initializeSmartConnections = async () => {
  // 检查 HTTP API 可用性
  try {
    await axios.get(`${HTTP_API_BASE_URL}/health`, { timeout: 3000 })
    smartAnalysisStatus.value.http = true
    console.log('智能分析 HTTP API 连接成功')
  } catch (error) {
    smartAnalysisStatus.value.http = false
    console.log('智能分析 HTTP API 连接失败:', error.message)
  }

  // 尝试建立 WebSocket 连接
  try {
    smartSocket = io(WEBSOCKET_URL, {
      timeout: 3000,
      transports: ['websocket', 'polling']
    })

    smartSocket.on('connect', () => {
      smartAnalysisStatus.value.websocket = true
      console.log('🔥 [调试] 智能分析 WebSocket 连接成功')
    })

    smartSocket.on('disconnect', () => {
      smartAnalysisStatus.value.websocket = false
      console.log('🔥 [调试] 智能分析 WebSocket 连接断开')
    })

    smartSocket.on('connect_error', (error) => {
      smartAnalysisStatus.value.websocket = false
      console.log('🔥 [调试] 智能分析 WebSocket 连接错误:', error.message)
    })

    // 添加分析进度监听器
    smartSocket.on('analysis_progress', (data) => {
      console.log('🔥 [调试] 收到分析进度更新:', data)
      updateSmartProgressData(data)
    })

    smartSocket.on('stage_completed', (data) => {
      console.log('🔥 [调试] 收到阶段完成事件:', data)
      if (data.stage && smartStageStatus.value[data.stage]) {
        smartStageStatus.value[data.stage] = 'completed'
        smartStageProgress.value[data.stage] = 100
        smartRunningStages.value.delete(data.stage)
        
        // 强制触发响应式更新
        smartStageProgress.value = { ...smartStageProgress.value }
        smartStageStatus.value = { ...smartStageStatus.value }
      }
    })

    smartSocket.on('analysis_completed', (data) => {
      console.log('🔥 [调试] 收到分析完成事件:', data)
      smartCurrentStage.value = 'completed'
      
      // 确保所有阶段都标记为完成
      Object.keys(smartStageStatus.value).forEach(stage => {
        smartStageStatus.value[stage] = 'completed'
        smartStageProgress.value[stage] = 100
      })
      
      smartRunningStages.value.clear()
      
      // 强制触发响应式更新
      smartStageProgress.value = { ...smartStageProgress.value }
      smartStageStatus.value = { ...smartStageStatus.value }
      
      ElMessage.success('智能分析已完成！')
    })

    // 通用事件监听器 - 用于调试
    smartSocket.onAny((eventName, ...args) => {
      console.log('🔥 [调试] 收到WebSocket事件:', eventName, args)
    })

  } catch (error) {
    smartAnalysisStatus.value.websocket = false
    console.log('智能分析 WebSocket 初始化失败:', error.message)
  }
}

// 智能文件上传处理
const handleSmartFileUpload = async (file) => {
  try {
    console.log('🔥 [调试] 开始智能文件上传:', file.name)
    console.log('🔥 [调试] 通信模式:', communicationMode.value)
    console.log('🔥 [调试] 执行模式:', smartAnalysisMode.value)
    
    const fileContent = await readSmartFileAsText(file)
    
    const requestData = {
      execution_mode: smartAnalysisMode.value,
      file_name: file.name,
      file_content: fileContent
    }

    let response
    if (communicationMode.value === 'websocket') {
      console.log('🔥 [调试] 使用WebSocket方式启动分析')
      response = await startSmartAnalysisWebSocket(requestData)
    } else {
      console.log('🔥 [调试] 使用HTTP方式启动分析')
      response = await startSmartAnalysisHttp(requestData)
    }
    
    console.log('🔥 [调试] 启动分析响应:', response)
    
    if (response.success) {
      smartAnalysisTaskId.value = response.task_id
      console.log('🔥 [调试] 分析任务ID:', smartAnalysisTaskId.value)
      
      ElMessage.success('智能分析任务已开始')
      
      if (smartAnalysisMode.value === 'automatic') {
        if (communicationMode.value === 'http') {
          console.log('🔥 [调试] 启动HTTP轮询')
          startSmartProgressPolling()
        } else {
          console.log('🔥 [调试] WebSocket模式，等待自动接收进度更新')
        }
      }
    } else {
      console.error('🔥 [调试] 启动分析失败:', response)
      ElMessage.error(response.error || '启动智能分析失败')
    }
  } catch (error) {
    console.error('🔥 [调试] 智能分析上传失败:', error)
    ElMessage.error('智能分析文件上传失败: ' + error.message)
  }
  
  return false // 阻止自动上传
}

const readSmartFileAsText = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = e => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsText(file, 'utf-8')
  })
}

// WebSocket 方式启动分析
const startSmartAnalysisWebSocket = (data) => {
  return new Promise((resolve, reject) => {
    if (!smartSocket || !smartSocket.connected) {
      reject(new Error('WebSocket 未连接'))
      return
    }
    
    smartSocket.emit('start_analysis', data)
    
    const timeoutId = setTimeout(() => {
      reject(new Error('WebSocket 请求超时'))
    }, 10000)

    const handleResponse = (response) => {
      clearTimeout(timeoutId)
      smartSocket.off('analysis_started', handleResponse)
      if (response.success) {
        resolve(response)
      } else {
        reject(new Error(response.error || '启动分析失败'))
      }
    }

    smartSocket.on('analysis_started', handleResponse)
  })
}

// HTTP 方式启动分析
const startSmartAnalysisHttp = async (data) => {
  console.log('🔥 [调试] HTTP启动分析请求:', data)
  const response = await axios.post(`${HTTP_API_BASE_URL}/v2/analysis/start`, data)
  console.log('🔥 [调试] HTTP启动分析响应:', response.data)
  return response.data
}

// 启动单个阶段
const startSmartStage = async (stage) => {
  try {
    smartRunningStages.value.add(stage)
    
    let response
    if (communicationMode.value === 'websocket') {
      response = await startSmartStageWebSocket({
        task_id: smartAnalysisTaskId.value,
        stage: stage
      })
    } else {
      response = await startSmartStageHttp({
        task_id: smartAnalysisTaskId.value,
        stage: stage
      })
    }
    
    if (response.success) {
      ElMessage.success(`${stage} 阶段已开始`)
      smartStageStatus.value[stage] = 'running'
      
      if (communicationMode.value === 'http') {
        startSmartProgressPolling()
      }
    } else {
      ElMessage.error(response.error || `启动 ${stage} 失败`)
      smartRunningStages.value.delete(stage)
    }
  } catch (error) {
    console.error(`启动阶段失败:`, error)
    ElMessage.error(`启动 ${stage} 阶段失败: ${error.message}`)
    smartRunningStages.value.delete(stage)
  }
}

const startSmartStageWebSocket = (data) => {
  return new Promise((resolve, reject) => {
    if (!smartSocket || !smartSocket.connected) {
      reject(new Error('WebSocket 未连接'))
      return
    }
    
    smartSocket.emit('trigger_stage', data)
    
    const timeoutId = setTimeout(() => {
      reject(new Error('WebSocket 请求超时'))
    }, 10000)

    const handleResponse = (response) => {
      clearTimeout(timeoutId)
      smartSocket.off('stage_started', handleResponse)
      if (response.success) {
        resolve(response)
      } else {
        reject(new Error(response.error || '启动阶段失败'))
      }
    }

    smartSocket.on('stage_started', handleResponse)
  })
}

const startSmartStageHttp = async (data) => {
  console.log('🔥 [调试] HTTP启动阶段请求:', data)
  const response = await axios.post(`${HTTP_API_BASE_URL}/v2/analysis/stage`, data)
  console.log('🔥 [调试] HTTP启动阶段响应:', response.data)
  return response.data
}

// 刷新进度
const refreshSmartProgress = async () => {
  if (!smartAnalysisTaskId.value) return
  
  refreshingSmartProgress.value = true
  try {
    let response
    if (communicationMode.value === 'websocket') {
      response = await getSmartProgressWebSocket(smartAnalysisTaskId.value)
    } else {
      response = await getSmartProgressHttp(smartAnalysisTaskId.value)
    }
    
    if (response.success) {
      updateSmartProgressData(response.data)
    }
  } catch (error) {
    console.error('刷新智能分析进度失败:', error)
    ElMessage.error('刷新进度失败: ' + error.message)
  } finally {
    refreshingSmartProgress.value = false
  }
}

const getSmartProgressWebSocket = (taskId) => {
  return new Promise((resolve, reject) => {
    if (!smartSocket || !smartSocket.connected) {
      reject(new Error('WebSocket 未连接'))
      return
    }
    
    smartSocket.emit('get_analysis_progress', { task_id: taskId })
    
    const timeoutId = setTimeout(() => {
      reject(new Error('WebSocket 请求超时'))
    }, 5000)

    const handleResponse = (response) => {
      clearTimeout(timeoutId)
      smartSocket.off('analysis_progress', handleResponse)
      if (response.success) {
        resolve(response)
      } else {
        reject(new Error(response.error || '获取进度失败'))
      }
    }

    smartSocket.on('analysis_progress', handleResponse)
  })
}

const getSmartProgressHttp = async (taskId) => {
  console.log('🔥 [调试] HTTP获取进度:', taskId)
  const response = await axios.get(`${HTTP_API_BASE_URL}/v2/analysis/progress/${taskId}`)
  console.log('🔥 [调试] HTTP获取进度响应:', response.data)
  return response.data
}

// 更新进度数据
const updateSmartProgressData = (data) => {
  console.log('🔥 [调试] 更新智能分析进度数据:', data)
  
  // 更新进度
  if (data.progress) {
    console.log('🔥 [调试] 当前进度状态:', smartStageProgress.value)
    Object.keys(smartStageProgress.value).forEach(stage => {
      if (data.progress[stage] !== undefined) {
        const oldProgress = smartStageProgress.value[stage]
        smartStageProgress.value[stage] = data.progress[stage]
        console.log(`🔥 [调试] 阶段 ${stage} 进度更新: ${oldProgress} -> ${data.progress[stage]}`)
        
        // 更新状态
        if (data.progress[stage] === 0) {
          smartStageStatus.value[stage] = 'waiting'
        } else if (data.progress[stage] === 100) {
          smartStageStatus.value[stage] = 'completed'
          smartRunningStages.value.delete(stage)
          console.log(`🔥 [调试] 阶段 ${stage} 已完成`)
        } else {
          smartStageStatus.value[stage] = 'running'
          console.log(`🔥 [调试] 阶段 ${stage} 正在运行`)
        }
      }
    })
    
    // 强制触发响应式更新
    smartStageProgress.value = { ...smartStageProgress.value }
    smartStageStatus.value = { ...smartStageStatus.value }
    console.log('🔥 [调试] 更新后的进度状态:', smartStageProgress.value)
  }
  
  // 更新当前阶段
  if (data.current_stage) {
    console.log(`🔥 [调试] 当前阶段更新: ${smartCurrentStage.value} -> ${data.current_stage}`)
    smartCurrentStage.value = data.current_stage
  }
}

// 轮询进度
const startSmartProgressPolling = () => {
  if (communicationMode.value !== 'http') return
  
  if (smartProgressTimer) {
    clearInterval(smartProgressTimer)
  }
  
  smartProgressTimer = setInterval(async () => {
    await refreshSmartProgress()
    
    // 如果所有阶段都完成了，停止轮询
    if (isSmartAllCompleted.value) {
      clearInterval(smartProgressTimer)
      smartProgressTimer = null
    }
  }, 2000) // 每2秒轮询一次
}

const stopSmartProgressPolling = () => {
  if (smartProgressTimer) {
    clearInterval(smartProgressTimer)
    smartProgressTimer = null
  }
}

// 查看结果
const viewSmartResults = async () => {
  try {
    let response
    if (communicationMode.value === 'websocket') {
      response = await getSmartResultsWebSocket(smartAnalysisTaskId.value)
    } else {
      response = await getSmartResultsHttp(smartAnalysisTaskId.value)
    }
    
    if (response.success) {
      smartAnalysisResults.value = response.data
      showSmartResults.value = true
    } else {
      ElMessage.error('获取智能分析结果失败')
    }
  } catch (error) {
    console.error('获取智能分析结果失败:', error)
    ElMessage.error('获取结果失败: ' + error.message)
  }
}

const getSmartResultsWebSocket = (taskId) => {
  return new Promise((resolve, reject) => {
    if (!smartSocket || !smartSocket.connected) {
      reject(new Error('WebSocket 未连接'))
      return
    }
    
    // WebSocket 获取结果的实现
    getSmartProgressWebSocket(taskId).then(progressResponse => {
      if (progressResponse.data && progressResponse.data.results) {
        resolve({
          success: true,
          data: progressResponse.data.results
        })
      } else {
        reject(new Error('结果不完整'))
      }
    }).catch(reject)
  })
}

const getSmartResultsHttp = async (taskId) => {
  const response = await axios.get(`${HTTP_API_BASE_URL}/v2/analysis/result/${taskId}`)
  return response.data
}

// 导出结果
const exportSmartResults = async () => {
  try {
    let response
    if (communicationMode.value === 'websocket') {
      // WebSocket 模式下导出，回退到 HTTP API
      response = await exportSmartResultsHttp(smartAnalysisTaskId.value)
    } else {
      response = await exportSmartResultsHttp(smartAnalysisTaskId.value)
    }
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `smart_analysis_result_${smartAnalysisTaskId.value}.md`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('智能分析结果已导出')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败: ' + error.message)
  }
}

const exportSmartResultsHttp = async (taskId) => {
  const response = await axios.get(`${HTTP_API_BASE_URL}/v2/analysis/export/${taskId}`, {
    responseType: 'blob'
  })
  return response
}

// 重置任务
const resetSmartTask = async () => {
  try {
    await ElMessageBox.confirm('确定要重新开始吗？当前进度将会丢失。', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    stopSmartProgressPolling()
    
    // 重置所有状态
    smartAnalysisTaskId.value = ''
    smartCurrentStage.value = ''
    showSmartResults.value = false
    
    Object.keys(smartStageProgress.value).forEach(stage => {
      smartStageProgress.value[stage] = 0
      smartStageStatus.value[stage] = 'waiting'
    })
    
    smartRunningStages.value.clear()
    smartAnalysisResults.value = {}
    
    ElMessage.success('智能分析已重置')
  } catch {
    // 用户取消
  }
}

// 智能分析辅助方法
const isSmartStageRunning = (stage) => {
  return smartRunningStages.value.has(stage)
}

const canStartSmartStage = (stage) => {
  if (stage === 'document_parsing') {
    return smartStageStatus.value[stage] === 'waiting' && !isSmartStageRunning(stage)
  } else if (stage === 'content_analysis') {
    return smartStageStatus.value['document_parsing'] === 'completed' && 
           smartStageStatus.value[stage] === 'waiting' && 
           !isSmartStageRunning(stage)
  } else if (stage === 'ai_analysis') {
    return smartStageStatus.value['content_analysis'] === 'completed' && 
           smartStageStatus.value[stage] === 'waiting' && 
           !isSmartStageRunning(stage)
  }
  return false
}

const getSmartStageStatusClass = (stage) => {
  const status = smartStageStatus.value[stage]
  return {
    'status-waiting': status === 'waiting',
    'status-running': status === 'running',
    'status-completed': status === 'completed',
    'status-error': status === 'error'
  }
}

const getSmartStageStatusText = (stage) => {
  const status = smartStageStatus.value[stage]
  const statusMap = {
    'waiting': '等待中',
    'running': '执行中',
    'completed': '已完成',
    'error': '出错'
  }
  return statusMap[status] || '未知'
}

const getSmartProgressStatus = (stage) => {
  const status = smartStageStatus.value[stage]
  if (status === 'completed') return 'success'
  if (status === 'error') return 'exception'
  if (status === 'running') return ''
  return ''
}

// ================== 原有方法 ==================

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// 监听上传文件变化
watch(uploadedFile, (newFile, oldFile) => {
  console.log('uploadedFile变化:', { newFile, oldFile })
}, { deep: true })

// 监听活动页签变化
watch(activeTab, (newTab, oldTab) => {
  console.log('activeTab变化:', { newTab, oldTab })
})

// 组件挂载时初始化
onMounted(() => {
  scrollToBottom()
  console.log('组件已挂载')
  console.log('初始uploadedFile:', uploadedFile.value)
  console.log('初始activeTab:', activeTab.value)
})

const getResultTypeTag = (type) => {
  switch (type) {
    case 'text': return 'primary'
    case 'word': return 'success'
    case 'pdf': return 'warning'
    default: return 'info'
  }
}

const getResultTypeText = (type) => {
  switch (type) {
    case 'text': return '文本文档'
    case 'word': return 'Word文档'
    case 'pdf': return 'PDF文档'
    default: return '文档解析'
  }
}

// 表格数据格式化
const formatTableData = (table) => {
  if (!table || !Array.isArray(table)) return []
  
  return table.map(row => {
    const rowData = {}
    row.forEach((cell, index) => {
      rowData[`col${index}`] = cell
    })
    return rowData
  })
}

const getTableColumns = (table) => {
  if (!table || !Array.isArray(table) || table.length === 0) return []
  return table[0] || []
}

// 内容操作方法
const copyContent = async () => {
  if (!analysisResult.value?.content) {
    ElMessage.warning('没有可复制的内容')
    return
  }
  
  try {
    await navigator.clipboard.writeText(analysisResult.value.content)
    ElMessage.success('内容已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const downloadContent = () => {
  if (!analysisResult.value?.content) {
    ElMessage.warning('没有可下载的内容')
    return
  }
  
  const blob = new Blob([analysisResult.value.content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${analysisResult.value.fileInfo?.name || 'document'}_content.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('内容下载开始')
}

const analyzeWithAI = async () => {
  if (!analysisResult.value?.content) {
    ElMessage.warning('没有可分析的内容')
    return
  }
  
  try {
    const message = `请分析以下文档内容：\n\n${analysisResult.value.content.substring(0, 2000)}${analysisResult.value.content.length > 2000 ? '...' : ''}`
    await wsStore.sendMessage(message)
    activeTab.value = 'realtime'
    ElMessage.success('已发送给AI进行智能处理')
  } catch (error) {
    ElMessage.error('发送分析请求失败')
  }
}

const exportResult = () => {
  ElMessage.info('导出功能开发中...')
}

const clearResult = () => {
  wsStore.clearAnalysisResult()
  ElMessage.success('解析结果已清空')
}

// 新增的辅助方法
const getDocumentTypeText = (type) => {
  const typeMap = {
    'requirements': '需求文档',
    'design': '设计文档',
    'general': '通用文档'
  }
  return typeMap[type] || '未知类型'
}

const getLanguageText = (language) => {
  const languageMap = {
    'chinese': '中文',
    'english': '英文',
    'unknown': '未知语言'
  }
  return languageMap[language] || language
}

const getAnalysisTypeText = (type) => {
  const typeMap = {
    'comprehensive': '全面分析',
    'summary': '摘要分析',
    'requirements': '需求分析',
    'custom': '自定义分析'
  }
  return typeMap[type] || type
}

const formatAIResponse = (response) => {
  if (!response) return ''
  
  return response
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/#{1,6}\s*(.*?)(?=\n|$)/g, '<h6>$1</h6>')
    .replace(/^\d+\.\s*(.*?)(?=\n|$)/gm, '<li>$1</li>')
    .replace(/^-\s*(.*?)(?=\n|$)/gm, '<li>$1</li>')
}
</script>

<style lang="scss" scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.sidebar {
  width: 400px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  height: 100vh;

  .sidebar-header {
    flex: 0 0 auto;
    padding: 20px;
    border-bottom: 1px solid #e4e7ed;
    background: white;

    .app-title {
      display: flex;
      align-items: center;
      margin: 0 0 16px 0;
      font-size: 20px;
      font-weight: 600;
      color: #303133;

      .el-icon {
        margin-right: 8px;
        color: #409eff;
      }
    }

    .new-chat-btn {
      width: 100%;
    }
  }

  .chat-history {
    flex: 0 0 auto;
    padding: 20px;
    overflow: hidden;

    .history-section {
      margin-bottom: 16px;

      h3 {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
        margin: 0 0 6px 0;
      }

      .section-subtitle {
        font-size: 14px;
        color: #909399;
        margin: 0;
      }
    }

    .task-description {
      margin-bottom: 16px;

      h4 {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin: 0 0 8px 0;
      }

      p {
        font-size: 13px;
        color: #606266;
        line-height: 1.5;
        margin: 0 0 8px 0;
      }
    }

    .feature-tips {
      margin-top: 12px;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      border: 1px solid #e4e7ed;

      p {
        font-size: 13px;
        color: #606266;
        font-weight: 500;
        margin: 0;
      }
    }
  }

  .chat-messages {
    flex: 1;
    padding: 15px 20px;
    overflow-y: auto;
    min-height: 0;

    .message {
      margin-bottom: 16px;

      &.user {
        .user-message {
          display: flex;
          flex-direction: column;
          align-items: flex-end;

          .message-content {
            background: #409eff;
            color: white;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
            max-width: 80%;
            word-wrap: break-word;
            font-size: 14px;
            line-height: 1.4;
          }

          .message-time {
            font-size: 12px;
            color: #909399;
            margin-top: 4px;
          }
        }
      }

      &.chat_response {
        .bot-message {
          display: flex;
          align-items: flex-start;

          .bot-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            flex-shrink: 0;

            .el-icon {
              color: #606266;
            }
          }

          .message-content {
            flex: 1;

            .message-text {
              background: white;
              padding: 12px 16px;
              border-radius: 4px 18px 18px 18px;
              border: 1px solid #e4e7ed;
              font-size: 14px;
              line-height: 1.6;
              color: #303133;
            }

            .message-time {
              font-size: 12px;
              color: #909399;
              margin-top: 4px;
            }
          }
        }
      }
    }

    .typing-indicator {
      display: flex;
      align-items: flex-start;

      .bot-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        flex-shrink: 0;

        .el-icon {
          color: #606266;
        }
      }

      .typing-dots {
        background: white;
        padding: 12px 16px;
        border-radius: 4px 18px 18px 18px;
        border: 1px solid #e4e7ed;
        display: flex;
        align-items: center;

        span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #c0c4cc;
          margin: 0 2px;
          animation: typing 1.4s infinite ease-in-out;

          &:nth-child(1) { animation-delay: -0.32s; }
          &:nth-child(2) { animation-delay: -0.16s; }
        }
      }
    }
  }

  .chat-input {
    flex: 0 0 auto;
    padding: 20px;
    border-top: 1px solid #e4e7ed;
    background: white;

    .input-container {
      .uploaded-file-info {
        display: flex;
        align-items: flex-start;
        margin-bottom: 12px;
        padding: 0;
        flex-wrap: wrap;
        gap: 8px;
        width: 100%;
        box-sizing: border-box;
        
        .file-info-container {
          display: flex;
          align-items: flex-start;
          flex: 1;
          min-width: 0;
          max-width: calc(100% - 80px);
          padding: 8px 12px;
          background: #f0f9ff;
          border: 1px solid #b3d8ff;
          border-radius: 6px;
          overflow: hidden;
          
          .file-icon {
            flex-shrink: 0;
            margin-right: 8px;
            margin-top: 2px;
            color: #67c23a;
          }
          
          .file-details {
            display: flex;
            flex-direction: column;
            min-width: 0;
            flex: 1;
            overflow: hidden;
            
            .file-name {
              word-break: break-all;
              overflow-wrap: break-word;
              line-height: 1.3;
              white-space: normal;
              font-size: 14px;
              color: #303133;
              margin-bottom: 2px;
            }
            
            .file-size {
              font-size: 12px;
              color: #909399;
              white-space: nowrap;
            }
          }
        }
        
        .close-btn {
          flex-shrink: 0;
          align-self: flex-start;
          margin-left: 6px;
          margin-top: 2px;
          padding: 4px;
          
          :deep(.el-icon) {
            font-size: 14px;
          }
        }
        
        .analyze-btn {
          flex-shrink: 0;
          align-self: flex-start;
          min-width: 72px;
        }
      }
      
      .input-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;
      }
    }
  }
}

.agent-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;

  .workspace-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid #e4e7ed;
    background: white;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  .workspace-tabs {
    flex: 1;
    padding: 0;
    overflow-y: auto;

    :deep(.el-tabs__header) {
      margin: 0;
      padding: 0 24px;
      background: #fafbfc;
      border-bottom: 1px solid #e4e7ed;
    }

    :deep(.el-tabs__content) {
      padding: 0;
      height: calc(100vh - 120px);
      overflow-y: auto;
    }

    .tab-content {
      padding: 24px;
      height: 100%;
      overflow-y: auto;

      .status-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;

        h4 {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
          margin: 0;
        }
      }

      .processing-steps {
        margin-bottom: 20px;

        :deep(.el-timeline-item__content) {
          .step-content {
            h5 {
              font-size: 14px;
              font-weight: 600;
              color: #303133;
              margin: 0 0 8px 0;
            }

            p {
              font-size: 13px;
              color: #606266;
              margin: 0 0 8px 0;
            }

            .step-progress {
              margin-top: 8px;
            }
          }
        }
      }

      .current-processing {
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .rotating {
            animation: rotate 2s linear infinite;
          }
        }
      }

      .analysis-result {
        .result-header {
          margin-bottom: 20px;

          h4 {
            font-size: 18px;
            font-weight: 600;
            color: #303133;
            margin: 0 0 8px 0;
          }

          .result-meta {
            display: flex;
            align-items: center;
            gap: 12px;

            .result-time {
              font-size: 13px;
              color: #909399;
            }
          }
        }

        .result-content {
          .info-card {
            margin-bottom: 16px;

            :deep(.el-card__header) {
              padding: 12px 16px;
              background: #fafbfc;

              h5 {
                font-size: 14px;
                font-weight: 600;
                color: #303133;
                margin: 0;
              }
            }

            :deep(.el-card__body) {
              padding: 16px;
            }

            .analysis-content {
              font-size: 14px;
              line-height: 1.6;
              color: #303133;

              h4 {
                font-size: 16px;
                font-weight: 600;
                color: #303133;
                margin: 16px 0 8px 0;
              }

              ul {
                margin: 8px 0;
                padding-left: 20px;
              }

              li {
                margin: 4px 0;
              }
            }

            .suggestions-content {
              ul {
                margin: 0;
                padding-left: 20px;

                li {
                  font-size: 14px;
                  color: #606266;
                  line-height: 1.6;
                  margin: 8px 0;
                }
              }
            }
          }
        }
      }

      .document-preview {
        .preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 12px;
          border-bottom: 1px solid #e4e7ed;

          h4 {
            font-size: 16px;
            font-weight: 600;
            color: #303133;
            margin: 0;
          }

          .file-info {
            display: flex;
            align-items: center;
            gap: 8px;

            .file-size {
              font-size: 12px;
              color: #909399;
            }
          }
        }

        .preview-content {
          .text-preview {
            .file-content {
              background: #f8f9fa;
              border: 1px solid #e4e7ed;
              border-radius: 6px;
              padding: 16px;
              margin-bottom: 20px;

              pre {
                margin: 0;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.5;
                color: #303133;
                white-space: pre-wrap;
                word-wrap: break-word;
              }
            }

            .loading-content {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              padding: 40px;
              color: #909399;

              .el-icon {
                font-size: 24px;
                margin-bottom: 12px;
              }

              p {
                margin: 0;
                font-size: 14px;
              }
            }
          }

          .binary-preview {
            .file-info-display {
              margin-bottom: 20px;

              .document-icon {
                display: flex;
                flex-direction: column;
                align-items: center;
                margin-bottom: 16px;

                .el-icon {
                  margin-bottom: 8px;
                }

                .icon-text {
                  font-size: 14px;
                  font-weight: 600;
                  color: #303133;
                  margin: 0;
                }
              }

              .preview-notice {
                margin-top: 16px;

                :deep(.el-alert__content) {
                  .notice-content {
                    p {
                      margin: 8px 0;
                      font-size: 13px;
                      line-height: 1.5;

                      strong {
                        color: #303133;
                        font-weight: 600;
                      }
                    }

                    ul {
                      margin: 8px 0;
                      padding-left: 20px;

                      li {
                        margin: 4px 0;
                        font-size: 13px;
                        line-height: 1.4;
                        color: #67c23a;
                      }
                    }
                  }
                }
              }
            }
          }

          .preview-actions {
            display: flex;
            justify-content: center;
            gap: 12px;
            padding-top: 20px;
            border-top: 1px solid #e4e7ed;
          }
        }
      }

      .empty-state {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 400px;
      }

      .export-options {
        .export-card {
          margin-bottom: 20px;

          :deep(.el-card__header) {
            padding: 16px 20px;
            background: #fafbfc;

            .card-header {
              display: flex;
              align-items: center;
              font-size: 16px;
              font-weight: 600;
              color: #303133;

              .el-icon {
                margin-right: 8px;
                color: #409eff;
              }
            }
          }

          :deep(.el-card__body) {
            padding: 20px;

            p {
              font-size: 14px;
              color: #606266;
              line-height: 1.6;
              margin: 0 0 16px 0;
            }

            .export-actions {
              display: flex;
              justify-content: flex-end;
              gap: 8px;
            }

            .custom-export {
              :deep(.el-checkbox-group) {
                display: flex;
                flex-direction: column;
                gap: 8px;
              }
            }
          }
        }
      }
    }
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: 50vh;
    
    .chat-input {
      .input-container {
        .uploaded-file-info {
          flex-direction: column;
          align-items: stretch;
          
          .file-info-container {
            max-width: 100%;
            margin-bottom: 8px;
            
            .file-details {
              .file-name {
                font-size: 13px;
              }
            }
          }
          
          .analyze-btn {
            width: 100%;
            align-self: stretch;
          }
        }
      }
    }
  }
  
  .agent-workspace {
    height: 50vh;
  }
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
  margin-top: 20px;
}

// 内容分析结果样式
.content-analysis-result {
  .analysis-section {
    margin-bottom: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #e4e7ed;
    }
    
    .summary-text {
      font-size: 14px;
      line-height: 1.6;
      color: #606266;
      margin: 0;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      border-left: 4px solid #409eff;
    }
    
    .keywords {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      
      .keyword-tag {
        margin: 0;
      }
    }
  }
}

// AI分析结果样式
.ai-analysis-result {
  .ai-analysis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    h5 {
      margin: 0;
    }
  }
  
  .ai-response-content {
    margin-top: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 12px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #e4e7ed;
    }
    
    .ai-response-text {
      background: #f8f9fa;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      padding: 16px;
      
      :deep(h6) {
        color: #409eff;
        font-weight: 600;
        margin: 16px 0 8px 0;
        
        &:first-child {
          margin-top: 0;
        }
      }
      
      :deep(strong) {
        color: #303133;
        font-weight: 600;
      }
      
      :deep(em) {
        color: #606266;
        font-style: italic;
      }
      
      :deep(code) {
        background: #e6f7ff;
        color: #1890ff;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
      }
      
      :deep(li) {
        margin: 4px 0;
        color: #606266;
        line-height: 1.5;
      }
    }
  }
  
  .custom-prompt-section {
    margin-top: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }
    
    .custom-prompt-text {
      font-size: 13px;
      color: #909399;
      background: #f5f7fa;
      padding: 8px 12px;
      border-radius: 4px;
      margin: 0;
      font-style: italic;
    }
  }
}

// ================== 智能分析样式 ==================

// 通信模式选择样式
.communication-mode {
  margin-bottom: 20px;
  
  .mode-selector {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #e1e8ed;
    
    h4 {
      margin: 0 0 15px 0;
      color: #2c3e50;
      text-align: center;
      font-size: 16px;
    }
    
    .mode-options {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-bottom: 15px;
      
      :deep(.el-radio) {
        margin-right: 0;
        
        .el-radio__label {
          padding-left: 0;
        }
      }
      
      .mode-option {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        border: 1px solid #ddd;
        border-radius: 6px;
        background: white;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: #409eff;
          box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
        }
        
        .el-icon {
          font-size: 18px;
          color: #409eff;
        }
        
        .mode-title {
          font-weight: 600;
          color: #2c3e50;
          font-size: 14px;
        }
        
        .mode-desc {
          font-size: 12px;
          color: #666;
        }
      }
    }
    
    .connection-status-indicators {
      display: flex;
      justify-content: center;
      gap: 20px;
      
      .status-item {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 4px;
        background: #fff2f0;
        color: #ff4d4f;
        font-size: 13px;
        
        &.connected {
          background: #f6ffed;
          color: #52c41a;
        }
        
        .el-icon {
          font-size: 14px;
        }
      }
    }
  }
}

// 智能分析任务样式
.smart-analysis-task {
  .task-info {
    margin-bottom: 20px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
    
    h4 {
      margin: 0 0 10px 0;
      color: #2c3e50;
      font-size: 16px;
    }
    
    .el-tag {
      margin-bottom: 5px;
    }
  }
  
  .analysis-stages {
    display: grid;
    gap: 16px;
    margin-bottom: 20px;
    
    .stage-card {
      border: 2px solid #e1e8ed;
      border-radius: 8px;
      padding: 16px;
      transition: all 0.3s ease;
      background: white;
      
      &.active {
        border-color: #409eff;
        box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
      }
      
      .stage-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        .stage-info {
          display: flex;
          align-items: center;
          gap: 12px;
          
          h5 {
            margin: 0;
            display: flex;
            align-items: center;
            gap: 6px;
            color: #2c3e50;
            font-size: 14px;
            
            .el-icon {
              font-size: 16px;
            }
          }
          
          .stage-status {
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 500;
            
            &.status-waiting {
              background: #f0f0f0;
              color: #666;
            }
            
            &.status-running {
              background: #e6f7ff;
              color: #1890ff;
            }
            
            &.status-completed {
              background: #f6ffed;
              color: #52c41a;
            }
            
            &.status-error {
              background: #fff2f0;
              color: #ff4d4f;
            }
          }
        }
      }
      
      .progress-container {
        margin-bottom: 8px;
      }
      
      .stage-description {
        color: #666;
        font-size: 13px;
      }
    }
  }
  
  .smart-control-buttons {
    display: flex;
    justify-content: center;
    gap: 12px;
  }
}

// 智能分析上传区域样式
.smart-upload-section {
  text-align: center;
  
  .upload-prompt {
    margin-bottom: 20px;
    
    h4 {
      margin: 0 0 8px 0;
      color: #2c3e50;
      font-size: 18px;
    }
    
    p {
      margin: 0;
      color: #666;
      font-size: 14px;
    }
  }
  
  .analysis-mode-selection {
    margin-bottom: 20px;
    
    h5 {
      margin: 0 0 10px 0;
      color: #2c3e50;
      font-size: 14px;
    }
    
    .mode-selection {
      display: flex;
      justify-content: center;
      gap: 20px;
    }
  }
  
  .smart-upload-area {
    .smart-upload {
      :deep(.el-upload) {
        width: 100%;
      }
      
      :deep(.el-upload-dragger) {
        width: 100%;
        height: 150px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }
    }
  }
}

// 智能分析结果样式
.smart-results-section {
  margin-top: 20px;
  
  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h4 {
      margin: 0;
      color: #2c3e50;
      font-size: 16px;
    }
  }
  
  .result-content {
    background: #f8f9fa;
    padding: 16px;
    border-radius: 6px;
    
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-all;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 12px;
      line-height: 1.4;
    }
  }
}

// 响应式设计适配
@media (max-width: 768px) {
  .communication-mode {
    .mode-selector {
      .mode-options {
        flex-direction: column;
        gap: 10px;
      }
      
      .connection-status-indicators {
        flex-direction: column;
        gap: 8px;
      }
    }
  }
  
  .smart-analysis-task {
    .analysis-stages {
      .stage-card {
        .stage-header {
          flex-direction: column;
          align-items: flex-start;
          gap: 8px;
        }
      }
    }
    
    .smart-control-buttons {
      flex-direction: column;
      align-items: center;
    }
  }
}
</style> 