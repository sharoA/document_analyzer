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
          <h3>需求文档智能体访谈提纲生成</h3>
          <p class="section-subtitle">用户研究专家</p>
        </div>
        
        <div class="task-description">
          <h4>问卷和访谈提纲编写</h4>
          <p>我能结合产品信息和研究目的，编写问卷和访谈提纲。具体做法是：</p>
          <ul>
            <li>充分理解产品定位和功能，明确产品面向的用户画像和主要使用场景。</li>
            <li>根据研究目的，设计针对性的问题。</li>
            <li>如果没有特殊要求，问卷问题总数约为30题，访谈提纲约为10题，可在1小时左右完成访谈。</li>
          </ul>
          <p>已向您介绍了我的主要能力，包括问卷分析、访谈记录总结和问卷与访谈提纲编写。如果您有相关需求，可以随时告诉我。</p>
        </div>
        
        <div class="task-status">
          <el-tag type="success" size="small">
            <el-icon><Check /></el-icon>
            已完成本次任务
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="main-chat">
      <!-- 顶部工具栏 -->
      <div class="chat-header">
        <div class="header-left">
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
        
        <div class="header-right">
          <el-button-group>
            <el-button size="small" @click="toggleRealtime">
              <el-icon><Microphone /></el-icon>
              实时问答
            </el-button>
            <el-button size="small" @click="showFiles">
              <el-icon><Document /></el-icon>
              文件
            </el-button>
          </el-button-group>
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
              <div v-if="message.analysis" class="analysis-info">
                <el-tag size="small" type="info">
                  置信度: {{ (message.analysis.confidence * 100).toFixed(1) }}%
                </el-tag>
              </div>
            </div>
          </div>
          
          <div v-else-if="message.type === 'processing'" class="processing-message">
            <div class="bot-avatar">
              <el-icon class="rotating"><Loading /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.message }}</div>
            </div>
          </div>
          
          <div v-else-if="message.type === 'system'" class="system-message">
            <el-alert 
              :title="message.message" 
              type="info" 
              :closable="false"
              show-icon
            />
          </div>
          
          <div v-else-if="message.type === 'error'" class="error-message">
            <el-alert 
              :title="message.message" 
              type="error" 
              :closable="false"
              show-icon
            />
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <div class="input-container">
          <el-input
            v-model="currentMessage"
            type="textarea"
            :rows="3"
            placeholder="请输入您的问题..."
            @keydown.ctrl.enter="sendMessage"
            :disabled="!isConnected"
            class="message-input"
          />
          <div class="input-actions">
            <div class="input-tips">
              <span>Ctrl + Enter 发送</span>
            </div>
            <el-button 
              type="primary" 
              :icon="Promotion"
              @click="sendMessage"
              :loading="isSending"
              :disabled="!isConnected || !currentMessage.trim()"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧面板（可选） -->
    <div class="right-panel" v-if="showRightPanel">
      <div class="panel-header">
        <h4>分析详情</h4>
        <el-button 
          size="small" 
          text 
          @click="showRightPanel = false"
          :icon="Close"
        />
      </div>
      <div class="panel-content">
        <!-- 这里可以显示详细的分析结果 -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useWebSocketStore } from '../stores/websocket'
import { 
  Plus, 
  ChatDotRound, 
  Check, 
  Connection, 
  Microphone, 
  Document, 
  User,
  Loading, 
  Promotion,
  Close
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const wsStore = useWebSocketStore()
const messagesContainer = ref(null)
const currentMessage = ref('')
const isSending = ref(false)
const showRightPanel = ref(false)

// 计算属性
const messages = computed(() => wsStore.messages)
const isConnected = computed(() => wsStore.isConnected)
const connectionStatus = computed(() => wsStore.connectionStatus)

const connectionStatusType = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return 'success'
    case 'connecting': return 'warning'
    case 'error': return 'danger'
    default: return 'info'
  }
})

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return '已连接'
    case 'connecting': return '连接中'
    case 'error': return '连接错误'
    default: return '未连接'
  }
})

// 方法
const sendMessage = async () => {
  if (!currentMessage.value.trim() || !isConnected.value) return
  
  isSending.value = true
  
  try {
    await wsStore.sendMessage(currentMessage.value)
    currentMessage.value = ''
    await scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
  } finally {
    isSending.value = false
  }
}

const startNewChat = () => {
  wsStore.clearMessages()
  ElMessage.success('已开始新的对话')
}

const toggleRealtime = () => {
  ElMessage.info('实时问答功能开发中')
}

const showFiles = () => {
  ElMessage.info('文件管理功能开发中')
}

// 简化时间格式化函数，不依赖dayjs
const formatTime = (timestamp) => {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    })
  } catch (error) {
    return '时间格式错误'
  }
}

const formatMessage = (message) => {
  // 简单的 Markdown 渲染
  return message
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

onMounted(() => {
  scrollToBottom()
})
</script>

<style lang="scss" scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.sidebar {
  width: 320px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;

  .sidebar-header {
    padding: 20px;
    border-bottom: 1px solid #e4e7ed;

    .app-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 16px 0;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }

    .new-chat-btn {
      width: 100%;
    }
  }

  .chat-history {
    flex: 1;
    padding: 20px;
    overflow-y: auto;

    .history-section {
      margin-bottom: 20px;

      h3 {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
        margin: 0 0 4px 0;
      }

      .section-subtitle {
        color: #909399;
        font-size: 14px;
        margin: 0;
      }
    }

    .task-description {
      margin-bottom: 20px;

      h4 {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin: 0 0 8px 0;
      }

      p {
        font-size: 14px;
        color: #606266;
        line-height: 1.5;
        margin: 0 0 8px 0;
      }

      ul {
        margin: 8px 0;
        padding-left: 20px;

        li {
          font-size: 14px;
          color: #606266;
          line-height: 1.5;
          margin-bottom: 4px;
        }
      }
    }

    .task-status {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}

.main-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;

  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid #e4e7ed;
    background: white;

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;

      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
    }
  }

  .chat-messages {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    background: #fafbfc;

    .message {
      margin-bottom: 20px;

      &.user {
        display: flex;
        justify-content: flex-end;

        .user-message {
          max-width: 70%;
          background: #409eff;
          color: white;
          padding: 12px 16px;
          border-radius: 12px;
          border-bottom-right-radius: 4px;

          .message-content {
            margin-bottom: 4px;
            line-height: 1.5;
          }

          .message-time {
            font-size: 12px;
            opacity: 0.8;
          }
        }
      }

      &.chat_response, &.processing {
        display: flex;
        align-items: flex-start;
        gap: 12px;

        .bot-avatar {
          width: 32px;
          height: 32px;
          background: #f0f9ff;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #409eff;
          flex-shrink: 0;

          .rotating {
            animation: rotate 1s linear infinite;
          }
        }

        .message-content {
          flex: 1;
          background: white;
          padding: 12px 16px;
          border-radius: 12px;
          border-top-left-radius: 4px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

          .message-text {
            line-height: 1.6;
            margin-bottom: 8px;
          }

          .message-time {
            font-size: 12px;
            color: #909399;
          }

          .analysis-info {
            margin-top: 8px;
          }
        }
      }

      &.system, &.error {
        margin: 16px 0;
      }
    }
  }

  .chat-input {
    padding: 20px;
    background: white;
    border-top: 1px solid #e4e7ed;

    .input-container {
      .message-input {
        margin-bottom: 12px;
      }

      .input-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .input-tips {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }
}

.right-panel {
  width: 300px;
  background: white;
  border-left: 1px solid #e4e7ed;

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid #e4e7ed;

    h4 {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
    }
  }

  .panel-content {
    padding: 20px;
  }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// 响应式设计
@media (max-width: 768px) {
  .chat-container {
    .sidebar {
      width: 280px;
    }
    
    .right-panel {
      display: none;
    }
  }
}
</style> 