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
          :icon="Plus" 
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
                <p>{{ currentProcessing }}</p>
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
                      <el-icon style="margin-right: 8px;"><View /></el-icon>
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

        <!-- 文件解析结果 -->
        <el-tab-pane label="解析结果" name="files">
          <div class="tab-content">
            <div v-if="!analysisResult" class="empty-state">
              <el-empty description="暂无解析结果">
                <el-button type="primary" @click="activeTab = 'realtime'">
                  上传文档开始分析
                </el-button>
              </el-empty>
            </div>
            
            <div v-else class="analysis-result">
              <div class="result-header">
                <h4>{{ analysisResult.title || '需求文档分析报告' }}</h4>
                <div class="result-meta">
                  <el-tag size="small">{{ analysisResult.type || '需求分析' }}</el-tag>
                  <span class="result-time">{{ formatTime(analysisResult.timestamp) }}</span>
                </div>
              </div>
              
              <el-scrollbar height="500px">
                <div class="result-content">
                  <!-- 基本信息 -->
                  <el-card class="info-card" v-if="analysisResult.basicInfo">
                    <template #header>
                      <h5>基本信息</h5>
                    </template>
                    <el-descriptions :column="2" border>
                      <el-descriptions-item 
                        v-for="(value, key) in analysisResult.basicInfo" 
                        :key="key"
                        :label="key"
                      >
                        {{ value }}
                      </el-descriptions-item>
                    </el-descriptions>
                  </el-card>
                  
                  <!-- 需求方信息 -->
                  <el-card class="info-card" v-if="analysisResult.clientInfo">
                    <template #header>
                      <h5>需求方信息</h5>
                    </template>
                    <el-descriptions :column="2" border>
                      <el-descriptions-item 
                        v-for="(value, key) in analysisResult.clientInfo" 
                        :key="key"
                        :label="key"
                      >
                        {{ value }}
                      </el-descriptions-item>
                    </el-descriptions>
                  </el-card>
                  
                  <!-- 详细分析 -->
                  <el-card class="info-card" v-if="analysisResult.analysis">
                    <template #header>
                      <h5>详细分析</h5>
                    </template>
                    <div class="analysis-content" v-html="formatMessage(analysisResult.analysis)"></div>
                  </el-card>
                  
                  <!-- 建议和改进 -->
                  <el-card class="info-card" v-if="analysisResult.suggestions">
                    <template #header>
                      <h5>建议和改进</h5>
                    </template>
                    <div class="suggestions-content">
                      <ul>
                        <li v-for="suggestion in analysisResult.suggestions" :key="suggestion">
                          {{ suggestion }}
                        </li>
                      </ul>
                    </div>
                  </el-card>
                </div>
              </el-scrollbar>
            </div>
          </div>
        </el-tab-pane>

        <!-- 导出功能 -->
        <el-tab-pane label="终端" name="export">
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
                    <el-checkbox label="basicInfo">基本信息</el-checkbox>
                    <el-checkbox label="clientInfo">需求方信息</el-checkbox>
                    <el-checkbox label="analysis">详细分析</el-checkbox>
                    <el-checkbox label="suggestions">建议和改进</el-checkbox>
                    <el-checkbox label="chat">对话记录</el-checkbox>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useWebSocketStore } from '../stores/websocket'
import { 
  Plus, 
  ChatDotRound, 
  User, 
  Connection, 
  Microphone, 
  Document, 
  Check,
  Loading, 
  Promotion,
  Close,
  Paperclip,
  FullScreen,
  Setting,
  Download,
  View,
  InfoFilled,
  ArrowLeft,
  ArrowRight,
  ZoomIn,
  ZoomOut
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

// 计算属性
const messages = computed(() => wsStore.messages)
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
  return typeMap[file.raw.type] || '未知文档类型'
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
  
  console.log('文件类型:', file.raw.type)
  console.log('文件名:', file.name)
  console.log('文件大小:', file.size)
  
  if (!allowedTypes.includes(file.raw.type) && !file.name.match(/\.(doc|docx|pdf|txt|md)$/i)) {
    ElMessage.error('不支持的文件格式，请上传 Word、PDF、TXT 或 Markdown 文件')
    return false
  }
  
  if (file.size > 50 * 1024 * 1024) { // 50MB
    ElMessage.error('文件大小不能超过 50MB')
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
  
  ElMessage.success(`文件 ${file.name} 已选择，点击"开始分析"进行处理`)
}

const removeFile = () => {
  uploadedFile.value = null
  uploadRef.value?.clearFiles()
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
    
    // 添加文档上传完成步骤
    wsStore.updateProcessingStep({
      id: 'step_0',
      title: '文档上传',
      description: `文件上传完成: ${uploadedFile.value.name}`,
      status: 'success',
      timestamp: new Date().toLocaleTimeString(),
      progress: 100
    })
    
    // 模拟文档分析过程
    await simulateDocumentAnalysis()
    
    ElMessage.success('文档分析完成')
    activeTab.value = 'files'
  } catch (error) {
    ElMessage.error('文档分析失败: ' + error.message)
  } finally {
    isAnalyzing.value = false
  }
}

const simulateDocumentAnalysis = async () => {
  const steps = [
    { id: 'step_1', title: '文档解析', description: '正在解析文档结构和内容', progress: 20 },
    { id: 'step_2', title: '内容分析', description: '正在分析需求内容', progress: 50 },
    { id: 'step_3', title: '智能处理', description: '正在生成分析报告', progress: 80 },
    { id: 'step_4', title: '完成处理', description: '分析报告生成完成', progress: 100 }
  ]
  
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i]
    
    // 添加或更新当前步骤
    wsStore.updateProcessingStep({
      id: step.id,
      title: step.title,
      description: step.description,
      status: 'primary',
      timestamp: new Date().toLocaleTimeString(),
      progress: step.progress
    })
    
    wsStore.setCurrentProcessing(step.description)
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 将当前步骤标记为完成
    wsStore.updateProcessingStep({
      id: step.id,
      title: step.title,
      description: i === steps.length - 1 ? step.description : `${step.title}完成`,
      status: 'success',
      timestamp: new Date().toLocaleTimeString(),
      progress: 100
    })
    
    // 如果不是最后一步，稍微延迟一下显示完成状态
    if (i < steps.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 500))
    }
  }
  
  // 设置分析结果
  wsStore.setAnalysisResult({
    title: '需求文档分析报告',
    type: '需求分析',
    timestamp: Date.now(),
    basicInfo: {
      '文档标题': uploadedFile.value.name.replace(/\.[^/.]+$/, ""),
      '版本': 'V0.1',
      '撰写人': '李威明',
      '类型': '系统对接',
      '标签': '链数, 民生银行'
    },
    clientInfo: {
      '日期': '2025/5/12',
      '需求人': '哈治均'
    },
    analysis: `
      <h4>需求概述</h4>
      <p>本文档描述了民生银行融资像范围调整的系统对接需求。主要涉及以下几个方面：</p>
      <ul>
        <li>系统架构设计与优化</li>
        <li>数据接口规范定义</li>
        <li>安全性要求与实现</li>
        <li>性能指标与监控</li>
      </ul>
      
      <h4>技术分析</h4>
      <p>基于文档内容分析，建议采用以下技术方案：</p>
      <ul>
        <li>微服务架构，提高系统可扩展性</li>
        <li>RESTful API设计，确保接口标准化</li>
        <li>OAuth 2.0认证，保障数据安全</li>
        <li>Redis缓存，优化系统性能</li>
      </ul>
    `,
    suggestions: [
      '建议增加详细的错误处理机制',
      '需要完善系统监控和日志记录',
      '建议添加自动化测试用例',
      '需要制定详细的部署和运维方案'
    ]
  })
  
  wsStore.setCurrentProcessing(null)
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
</style> 