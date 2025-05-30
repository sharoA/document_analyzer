<template>
  <div class="simple-pdf-preview">
    <div v-if="isLoading" class="loading-container">
      <el-icon class="rotating" size="24"><Loading /></el-icon>
      <p>正在加载PDF文档...</p>
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-alert
        title="PDF预览失败"
        type="error"
        :description="error"
        show-icon
        :closable="false"
      />
      <div style="margin-top: 16px;">
        <el-button @click="tryAlternativeMethod" type="primary">
          尝试其他预览方式
        </el-button>
      </div>
    </div>
    
    <div v-else-if="pdfUrl" class="pdf-container">
      <div class="pdf-toolbar">
        <span>PDF文档预览</span>
        <el-button-group>
          <el-button @click="downloadPdf" size="small">
            <el-icon><Download /></el-icon>
            下载
          </el-button>
          <el-button @click="openInNewTab" size="small">
            <el-icon><View /></el-icon>
            新窗口打开
          </el-button>
        </el-button-group>
      </div>
      
      <!-- 使用iframe预览PDF -->
      <iframe
        :src="pdfUrl"
        class="pdf-iframe"
        frameborder="0"
        @load="onIframeLoad"
        @error="onIframeError"
      ></iframe>
    </div>
    
    <div v-else class="empty-container">
      <el-empty description="无法预览PDF文档">
        <el-button @click="$emit('retry')" type="primary">
          重新尝试
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Download, View } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  file: {
    type: Object,
    required: true
  }
})

// Emits
const emit = defineEmits(['retry'])

// 响应式数据
const isLoading = ref(false)
const error = ref('')
const pdfUrl = ref('')

// 方法
const loadPdf = async () => {
  if (!props.file) return
  
  isLoading.value = true
  error.value = ''
  pdfUrl.value = ''
  
  try {
    // 创建Blob URL
    const blob = new Blob([props.file.raw], { type: 'application/pdf' })
    pdfUrl.value = URL.createObjectURL(blob)
    
    console.log('PDF Blob URL创建成功:', pdfUrl.value)
    ElMessage.success('PDF文档加载成功')
  } catch (err) {
    console.error('PDF加载失败:', err)
    error.value = err.message || '无法加载PDF文档'
    ElMessage.error('PDF文档加载失败')
  } finally {
    isLoading.value = false
  }
}

const onIframeLoad = () => {
  console.log('PDF iframe加载成功')
}

const onIframeError = () => {
  console.error('PDF iframe加载失败')
  error.value = '浏览器不支持PDF预览，请下载文档查看'
}

const downloadPdf = () => {
  if (!pdfUrl.value) return
  
  const a = document.createElement('a')
  a.href = pdfUrl.value
  a.download = props.file.name
  a.click()
}

const openInNewTab = () => {
  if (!pdfUrl.value) return
  window.open(pdfUrl.value, '_blank')
}

const tryAlternativeMethod = () => {
  // 尝试重新加载
  loadPdf()
}

// 监听文件变化
watch(() => props.file, (newFile) => {
  if (newFile) {
    loadPdf()
  }
}, { immediate: true })

// 清理资源
onUnmounted(() => {
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value)
  }
})
</script>

<style lang="scss" scoped>
.simple-pdf-preview {
  width: 100%;
  height: 100%;
  
  .loading-container, .error-container, .empty-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    text-align: center;
    
    .el-icon {
      margin-bottom: 12px;
      color: #409eff;
    }
    
    p {
      margin: 0;
      color: #606266;
      font-size: 14px;
    }
  }
  
  .pdf-container {
    width: 100%;
    height: 600px;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    overflow: hidden;
    
    .pdf-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: #f5f7fa;
      border-bottom: 1px solid #e4e7ed;
      
      span {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
      }
    }
    
    .pdf-iframe {
      width: 100%;
      height: calc(100% - 49px);
      border: none;
    }
  }
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.rotating {
  animation: rotating 2s linear infinite;
}
</style> 