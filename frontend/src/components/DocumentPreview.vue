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
      <!-- PDF.js渲染方式 -->
      <div v-if="pdfSrc && !useFallback" class="pdf-container">
        <div class="pdf-controls">
          <el-button-group>
            <el-button @click="prevPage" :disabled="currentPage <= 1" size="small">
              <el-icon><ArrowLeft /></el-icon>
              上一页
            </el-button>
            <el-button @click="nextPage" :disabled="currentPage >= totalPages" size="small">
              下一页
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </el-button-group>
          <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
          <el-button-group>
            <el-button @click="zoomOut" size="small">
              <el-icon><ZoomOut /></el-icon>
            </el-button>
            <el-button @click="zoomIn" size="small">
              <el-icon><ZoomIn /></el-icon>
            </el-button>
          </el-button-group>
          <span class="zoom-info">{{ Math.round(scale * 100) }}%</span>
        </div>
        
        <div class="pdf-viewer" ref="pdfViewer">
          <canvas
            ref="pdfCanvas"
            :style="{ transform: `scale(${scale})`, transformOrigin: 'top left' }"
          ></canvas>
        </div>
      </div>
      
      <!-- 备选iframe预览方式 -->
      <div v-else-if="useFallback" class="fallback-preview">
        <div class="fallback-toolbar">
          <span>PDF文档预览（简化模式）</span>
          <el-button-group>
            <el-button @click="downloadPdf" size="small">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button @click="openInNewTab" size="small">
              <el-icon><View /></el-icon>
              新窗口打开
            </el-button>
            <el-button @click="retryPdfJs" size="small">
              <el-icon><Refresh /></el-icon>
              重试高级预览
            </el-button>
          </el-button-group>
        </div>
        
        <iframe
          v-if="pdfBlobUrl"
          :src="pdfBlobUrl"
          class="pdf-iframe"
          frameborder="0"
        ></iframe>
      </div>
      
      <div v-else-if="isLoading" class="loading-container">
        <el-icon class="rotating" size="24"><Loading /></el-icon>
        <p>正在加载PDF文档...</p>
      </div>
      <div v-else-if="error" class="error-container">
        <el-alert
          title="PDF文档加载失败"
          type="error"
          :description="error"
          show-icon
          :closable="false"
        />
        <div style="margin-top: 16px;">
          <el-button @click="tryFallbackPreview" type="primary">
            尝试简化预览
          </el-button>
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
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, ArrowLeft, ArrowRight, ZoomIn, ZoomOut, Download, View, Refresh } from '@element-plus/icons-vue'
import mammoth from 'mammoth'

// 动态导入PDF.js
let pdfjsLib = null

// Promise.withResolvers polyfill
if (!Promise.withResolvers) {
  Promise.withResolvers = function() {
    let resolve, reject
    const promise = new Promise((res, rej) => {
      resolve = res
      reject = rej
    })
    return { promise, resolve, reject }
  }
}

// 初始化PDF.js
const initPdfJs = async () => {
  if (pdfjsLib) return pdfjsLib
  
  try {
    pdfjsLib = await import('pdfjs-dist')
    
    // 尝试多种worker配置方法
    try {
      // 方法1: 使用本地worker
      pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
        'pdfjs-dist/build/pdf.worker.js',
        import.meta.url
      ).toString()
    } catch (e) {
      // 方法2: 使用CDN worker
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js'
    }
    
    console.log('PDF.js初始化成功，版本:', pdfjsLib.version)
    console.log('Worker路径:', pdfjsLib.GlobalWorkerOptions.workerSrc)
    return pdfjsLib
  } catch (error) {
    console.error('PDF.js初始化失败:', error)
    throw error
  }
}

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
const pdfSrc = ref(null)
const pdfDoc = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)
const pdfCanvas = ref(null)
const pdfViewer = ref(null)
const useFallback = ref(false)
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

// 方法
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

const loadPdfDocument = async () => {
  if (!props.file || !isPdfDocument.value) return
  
  console.log('开始加载PDF文档:', props.file.name)
  isLoading.value = true
  error.value = ''
  pdfSrc.value = false
  useFallback.value = false
  
  try {
    // 初始化PDF.js
    const pdfjs = await initPdfJs()
    
    const arrayBuffer = await props.file.raw.arrayBuffer()
    console.log('PDF文件读取成功，大小:', arrayBuffer.byteLength)
    
    const loadingTask = pdfjs.getDocument({ 
      data: arrayBuffer
    })
    
    pdfDoc.value = await loadingTask.promise
    console.log('PDF文档解析成功，页数:', pdfDoc.value.numPages)
    
    totalPages.value = pdfDoc.value.numPages
    currentPage.value = 1
    pdfSrc.value = true
    
    // 等待DOM更新后再渲染
    await nextTick()
    await renderPage(1)
    
    ElMessage.success(`PDF文档加载成功，共${totalPages.value}页`)
  } catch (err) {
    console.error('PDF.js加载失败:', err)
    console.log('尝试使用备选预览方式...')
    
    // 自动切换到备选方案
    try {
      await tryFallbackPreview()
    } catch (fallbackErr) {
      error.value = `PDF加载失败: ${err.message}`
      ElMessage.error('PDF文档加载失败')
    }
  } finally {
    isLoading.value = false
  }
}

const renderPage = async (pageNum) => {
  if (!pdfDoc.value) {
    console.error('PDF文档未加载')
    return
  }
  
  if (!pdfCanvas.value) {
    console.error('Canvas元素未找到')
    return
  }
  
  try {
    console.log('开始渲染第', pageNum, '页')
    const page = await pdfDoc.value.getPage(pageNum)
    const viewport = page.getViewport({ scale: 1.5 }) // 提高默认缩放比例
    
    const canvas = pdfCanvas.value
    const context = canvas.getContext('2d')
    
    // 设置canvas尺寸
    canvas.height = viewport.height
    canvas.width = viewport.width
    
    // 清除之前的内容
    context.clearRect(0, 0, canvas.width, canvas.height)
    
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }
    
    const renderTask = page.render(renderContext)
    await renderTask.promise
    
    currentPage.value = pageNum
    console.log('页面渲染成功:', pageNum)
  } catch (err) {
    console.error('PDF页面渲染失败:', err)
    error.value = `页面渲染失败: ${err.message}`
    ElMessage.error('PDF页面渲染失败')
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    renderPage(currentPage.value - 1)
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    renderPage(currentPage.value + 1)
  }
}

const zoomIn = () => {
  scale.value = Math.min(scale.value + 0.2, 3.0)
}

const zoomOut = () => {
  scale.value = Math.max(scale.value - 0.2, 0.5)
}

const downloadPdf = () => {
  if (!props.file) return
  
  const blob = new Blob([props.file.raw], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = props.file.name
  a.click()
  URL.revokeObjectURL(url)
}

const openInNewTab = () => {
  if (!pdfBlobUrl.value) {
    createPdfBlobUrl()
  }
  if (pdfBlobUrl.value) {
    window.open(pdfBlobUrl.value, '_blank')
  }
}

const retryPdfJs = () => {
  useFallback.value = false
  error.value = ''
  loadPdfDocument()
}

const tryFallbackPreview = async () => {
  console.log('尝试使用备选预览方式')
  useFallback.value = true
  error.value = ''
  
  try {
    await createPdfBlobUrl()
    ElMessage.success('已切换到简化预览模式')
  } catch (err) {
    console.error('备选预览失败:', err)
    error.value = '无法预览PDF文档，请下载查看'
  }
}

const createPdfBlobUrl = async () => {
  if (pdfBlobUrl.value) return
  
  try {
    const blob = new Blob([props.file.raw], { type: 'application/pdf' })
    pdfBlobUrl.value = URL.createObjectURL(blob)
    console.log('PDF Blob URL创建成功')
  } catch (err) {
    console.error('创建PDF Blob URL失败:', err)
    throw err
  }
}

// 监听文件变化
watch(() => props.file, async (newFile) => {
  if (!newFile) return
  
  if (isWordDocument.value) {
    await loadWordDocument()
  } else if (isPdfDocument.value) {
    await loadPdfDocument()
  }
}, { immediate: true })

// 组件挂载
onMounted(() => {
  // watch监听器已经设置了immediate: true，会在组件挂载时自动执行
  // 这里不需要重复调用加载方法
  console.log('DocumentPreview组件已挂载')
})

// 组件卸载
onUnmounted(() => {
  // 清理Blob URL
  if (pdfBlobUrl.value) {
    URL.revokeObjectURL(pdfBlobUrl.value)
    pdfBlobUrl.value = null
  }
  
  // 清理PDF文档
  if (pdfDoc.value) {
    pdfDoc.value.destroy()
    pdfDoc.value = null
  }
  
  console.log('DocumentPreview组件资源已清理')
})
</script>

<style lang="scss" scoped>
.document-preview-container {
  width: 100%;
  height: 100%;
  
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
    }
    
    p {
      margin: 0;
      color: #606266;
      font-size: 14px;
    }
  }
  
  .word-preview {
    .word-content {
      padding: 20px;
      background: white;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      max-height: 600px;
      overflow-y: auto;
      
      :deep(p) {
        margin: 8px 0;
        line-height: 1.6;
      }
      
      :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
        margin: 16px 0 8px 0;
        font-weight: 600;
      }
      
      :deep(ul), :deep(ol) {
        margin: 8px 0;
        padding-left: 20px;
      }
      
      :deep(table) {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        
        th, td {
          border: 1px solid #e4e7ed;
          padding: 8px 12px;
          text-align: left;
        }
        
        th {
          background: #f5f7fa;
          font-weight: 600;
        }
      }
    }
  }
  
  .pdf-preview {
    .pdf-controls {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: #f5f7fa;
      border: 1px solid #e4e7ed;
      border-bottom: none;
      border-radius: 6px 6px 0 0;
      
      .page-info, .zoom-info {
        font-size: 14px;
        color: #606266;
        margin: 0 12px;
      }
    }
    
    .pdf-viewer {
      border: 1px solid #e4e7ed;
      border-radius: 0 0 6px 6px;
      background: #f8f9fa;
      max-height: 600px;
      overflow: auto;
      padding: 20px;
      text-align: center;
      
      canvas {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        background: white;
      }
    }
    
    .fallback-preview {
      width: 100%;
      height: 600px;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      overflow: hidden;
      
      .fallback-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: #fff7e6;
        border-bottom: 1px solid #e4e7ed;
        
        span {
          font-size: 14px;
          font-weight: 600;
          color: #e6a23c;
        }
      }
      
      .pdf-iframe {
        width: 100%;
        height: calc(100% - 49px);
        border: none;
      }
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