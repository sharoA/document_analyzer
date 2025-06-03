<template>
  <div class="document-preview-container">
    <!-- Word文档预览 -->
    <div v-if="isWordDocument" class="word-preview">
      <div v-if="wordContent" class="word-content" v-html="wordContent"></div>
      <div v-else-if="isLoading" class="loading-container">
        <el-icon class="rotating" size="24"><Loading /></el-icon>
        <p>正在解析Word文档...</p>
      </div>
      <div v-else-if="error" class="error-container">
        <el-alert
          title="Word文档解析失败"
          type="error"
          :description="error"
          show-icon
          :closable="false"
        />
      </div>
    </div>

    <!-- PDF文档预览 -->
    <div v-else-if="isPdfDocument" class="pdf-preview">
      <!-- 简化的PDF预览工具栏 -->
      <div class="pdf-toolbar">
        <div class="toolbar-left">
          <span class="file-info">{{ props.file?.name || 'PDF文档' }}</span>
          <el-tag size="small" type="info">{{ formatFileSize(props.file?.size || 0) }}</el-tag>
        </div>
        <div class="toolbar-right">
          <el-button-group size="small">
            <el-button @click="downloadPdf" :icon="Download">下载</el-button>
            <el-button @click="openInNewTab" :icon="View">新窗口打开</el-button>
            <el-button @click="refreshPreview" :icon="Refresh">刷新</el-button>
          </el-button-group>
        </div>
      </div>

      <!-- PDF预览区域 -->
      <div class="pdf-content">
        <div v-if="isLoading" class="loading-container">
          <el-icon class="rotating" size="24"><Loading /></el-icon>
          <p>正在加载PDF文档...</p>
        </div>
        
        <div v-else-if="error" class="error-container">
          <el-alert
            title="PDF预览失败"
            type="warning"
            :description="error"
            show-icon
            :closable="false"
          />
          <div class="error-actions">
            <el-button type="primary" @click="downloadPdf" :icon="Download">
              下载文档查看
            </el-button>
            <el-button @click="refreshPreview" :icon="Refresh">
              重试预览
            </el-button>
          </div>
        </div>

        <div v-else-if="pdfBlobUrl" class="pdf-viewer">
          <iframe
            :src="pdfBlobUrl"
            class="pdf-iframe"
            frameborder="0"
            @load="onIframeLoad"
            @error="onIframeError"
          ></iframe>
        </div>
      </div>
    </div>

    <!-- 不支持的文档类型 -->
    <div v-else class="unsupported-container">
      <el-alert
        title="文档类型不支持预览"
        type="warning"
        description="当前文档类型不支持在线预览，请使用分析功能提取文档内容。"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Download, View, Refresh } from '@element-plus/icons-vue'
import mammoth from 'mammoth'

// Props
const props = defineProps({
  file: {
    type: Object,
    required: true
  }
})

// 响应式数据
const isLoading = ref(false)
const error = ref('')
const wordContent = ref('')
const pdfBlobUrl = ref(null)

// 计算属性
const isWordDocument = computed(() => {
  if (!props.file) return false
  const type = props.file.raw?.type || ''
  const name = props.file.name || ''
  return type.includes('word') || 
         type.includes('document') || 
         name.toLowerCase().endsWith('.doc') || 
         name.toLowerCase().endsWith('.docx')
})

const isPdfDocument = computed(() => {
  if (!props.file) return false
  const type = props.file.raw?.type || ''
  const name = props.file.name || ''
  return type === 'application/pdf' || name.toLowerCase().endsWith('.pdf')
})

// 工具函数
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// Word文档处理
const loadWordDocument = async () => {
  if (!props.file || !isWordDocument.value) return
  
  isLoading.value = true
  error.value = ''
  wordContent.value = ''
  
  try {
    const arrayBuffer = await props.file.raw.arrayBuffer()
    const result = await mammoth.convertToHtml({ arrayBuffer })
    
    if (result.messages.length > 0) {
      console.warn('Word转换警告:', result.messages)
    }
    
    wordContent.value = result.value
    ElMessage.success('Word文档加载成功')
  } catch (err) {
    console.error('Word文档加载失败:', err)
    error.value = err.message || '无法解析Word文档'
    ElMessage.error('Word文档加载失败')
  } finally {
    isLoading.value = false
  }
}

// PDF文档处理
const loadPdfDocument = async () => {
  if (!props.file || !isPdfDocument.value) return
  
  console.log('开始加载PDF文档:', props.file.name)
  isLoading.value = true
  error.value = ''
  
  try {
    // 清理之前的URL
    if (pdfBlobUrl.value) {
      URL.revokeObjectURL(pdfBlobUrl.value)
      pdfBlobUrl.value = null
    }
    
    // 创建新的Blob URL
    const blob = new Blob([props.file.raw], { type: 'application/pdf' })
    pdfBlobUrl.value = URL.createObjectURL(blob)
    
    console.log('PDF Blob URL创建成功:', pdfBlobUrl.value)
    ElMessage.success('PDF文档加载成功')
  } catch (err) {
    console.error('PDF文档加载失败:', err)
    error.value = `PDF加载失败: ${err.message || '未知错误'}`
    ElMessage.error('PDF文档加载失败')
  } finally {
    isLoading.value = false
  }
}

// 事件处理
const onIframeLoad = () => {
  console.log('PDF iframe加载成功')
}

const onIframeError = () => {
  console.error('PDF iframe加载失败')
  error.value = 'PDF预览失败，请尝试下载查看'
}

const downloadPdf = () => {
  if (!props.file) return
  
  try {
    const blob = new Blob([props.file.raw], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = props.file.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('文档下载开始')
  } catch (err) {
    console.error('下载失败:', err)
    ElMessage.error('下载失败')
  }
}

const openInNewTab = () => {
  if (pdfBlobUrl.value) {
    window.open(pdfBlobUrl.value, '_blank')
  } else {
    ElMessage.warning('请等待文档加载完成')
  }
}

const refreshPreview = () => {
  if (isPdfDocument.value) {
    loadPdfDocument()
  } else if (isWordDocument.value) {
    loadWordDocument()
  }
}

// 监听文件变化
watch(() => props.file, async (newFile) => {
  if (!newFile) return
  
  console.log('文件变化，开始加载:', newFile.name)
  
  if (isWordDocument.value) {
    await loadWordDocument()
  } else if (isPdfDocument.value) {
    await loadPdfDocument()
  }
}, { immediate: true })

// 组件挂载
onMounted(() => {
  console.log('DocumentPreview组件已挂载')
})

// 组件卸载
onUnmounted(() => {
  // 清理Blob URL
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
    pdfBlobUrl.value = null
  }
  console.log('DocumentPreview组件资源已清理')
})
</script>

<style lang="scss" scoped>
.document-preview-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .loading-container, .error-container, .unsupported-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    text-align: center;
    
    .el-icon {
      margin-bottom: 12px;
      color: #409eff;
      
      &.rotating {
        animation: rotate 2s linear infinite;
      }
    }
    
    p {
      margin: 8px 0;
      color: #666;
    }
  }
  
  .error-actions {
    margin-top: 16px;
    display: flex;
    gap: 12px;
    justify-content: center;
  }
  
  .word-preview {
    flex: 1;
    overflow: auto;
    
    .word-content {
      padding: 20px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      
      // Word内容样式
      :deep(p) {
        margin: 8px 0;
        line-height: 1.6;
      }
      
      :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
        margin: 16px 0 8px 0;
        color: #333;
      }
      
      :deep(table) {
        border-collapse: collapse;
        width: 100%;
        margin: 16px 0;
        
        th, td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        
        th {
          background-color: #f5f5f5;
          font-weight: bold;
        }
      }
    }
  }
  
  .pdf-preview {
    flex: 1;
    display: flex;
    flex-direction: column;
    
    .pdf-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: #f8f9fa;
      border-bottom: 1px solid #e9ecef;
      border-radius: 8px 8px 0 0;
      
      .toolbar-left {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .file-info {
          font-weight: 500;
          color: #333;
          max-width: 300px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
    
    .pdf-content {
      flex: 1;
      position: relative;
      background: #f5f5f5;
      
      .pdf-viewer {
        width: 100%;
        height: 100%;
        
        .pdf-iframe {
          width: 100%;
          height: 100%;
          border: none;
          background: white;
        }
      }
    }
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
</style> 