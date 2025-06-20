<template>
  <div class="image-display-demo">
    <el-card>
      <template #header>
        <div class="demo-header">
          <h4>图片显示功能演示</h4>
          <el-tag type="success">前端图片处理</el-tag>
        </div>
      </template>
      
      <div class="demo-content">
        <!-- 测试原始路径 -->
        <div class="test-section">
          <h5>1. 原始路径测试</h5>
          <div class="test-content" v-html="processedContent1"></div>
        </div>
        
        <!-- 测试图片引用格式 -->
        <div class="test-section">
          <h5>2. 图片引用格式测试</h5>
          <div class="test-content" v-html="processedContent2"></div>
        </div>
        
        <!-- 测试HTML img标签 -->
        <div class="test-section">
          <h5>3. HTML img标签测试</h5>
          <div class="test-content" v-html="processedContent3"></div>
        </div>
        
        <!-- 图片预加载状态 -->
        <div class="preload-status">
          <h5>图片预加载状态</h5>
          <el-table :data="preloadResults" size="small" border>
            <el-table-column prop="url" label="图片URL" show-overflow-tooltip />
            <el-table-column prop="accessible" label="可访问">
              <template #default="{ row }">
                <el-tag :type="row.accessible ? 'success' : 'danger'" size="small">
                  {{ row.accessible ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { processImagePaths, preloadImages } from '../utils/imageUtils'

// 测试数据
const testContent1 = ref('这是一个测试文本，包含图片路径：uploads/temp/8625cc95-e731-4040-ac08-0645b53230c3_需求文档_img_20250619_200647_1.png')

const testContent2 = ref('请查看 图片1(uploads/temp/example_image.png) 和 图片2(uploads/temp/test_image.jpg) 的内容。')

const testContent3 = ref('<p>这是一个包含img标签的测试：<img src="/uploads/temp/test.png" alt="测试图片" /></p>')

// 处理后的内容
const processedContent1 = ref('')
const processedContent2 = ref('')
const processedContent3 = ref('')

// 预加载结果
const preloadResults = ref([])

onMounted(async () => {
  // 处理测试内容
  processedContent1.value = processImagePaths(testContent1.value)
  processedContent2.value = processImagePaths(testContent2.value)
  processedContent3.value = processImagePaths(testContent3.value)
  
  // 预加载图片
  const allContent = [processedContent1.value, processedContent2.value, processedContent3.value].join(' ')
  preloadResults.value = await preloadImages(allContent)
  
  console.log('图片显示演示组件已加载')
  console.log('处理结果1:', processedContent1.value)
  console.log('处理结果2:', processedContent2.value)
  console.log('处理结果3:', processedContent3.value)
  console.log('预加载结果:', preloadResults.value)
})
</script>

<style lang="scss" scoped>
.image-display-demo {
  padding: 20px;
  
  .demo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    h4 {
      margin: 0;
      color: #303133;
    }
  }
  
  .demo-content {
    .test-section {
      margin-bottom: 24px;
      padding: 16px;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      background: #fafafa;
      
      h5 {
        margin: 0 0 12px 0;
        color: #409eff;
        font-weight: 600;
      }
      
      .test-content {
        background: white;
        padding: 12px;
        border-radius: 4px;
        border: 1px solid #e4e7ed;
        
        :deep(img) {
          max-width: 100%;
          height: auto;
          border: 1px solid #ddd;
          border-radius: 4px;
          margin: 8px 0;
        }
      }
    }
    
    .preload-status {
      margin-top: 24px;
      
      h5 {
        margin: 0 0 12px 0;
        color: #606266;
        font-weight: 600;
      }
    }
  }
}
</style> 