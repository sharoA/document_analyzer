/**
 * 图片处理工具
 * 用于前端处理和渲染分析结果中的图片
 */

// API基础URL配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * 处理文本中的图片路径，确保能够正确显示
 * @param {string} text - 包含图片路径的文本
 * @returns {string} - 处理后的HTML文本
 */
export function processImagePaths(text) {
  if (!text) return text
  
  try {
    // 处理已经转换为img标签的情况
    let processedText = text.replace(
      /<img\s+src="([^"]*uploads\/temp\/[^"]*)"([^>]*)>/g,
      (match, src, attributes) => {
        // 确保src是完整的URL
        const fullUrl = src.startsWith('http') ? src : `${API_BASE_URL}${src.startsWith('/') ? src : '/' + src}`
        return `<img src="${fullUrl}" ${attributes} onerror="this.style.display='none'" onload="this.style.display='inline-block'">`
      }
    )
    
    // 处理纯路径格式：uploads/temp/xxx.png
    processedText = processedText.replace(
      /(?<!src=["'])(uploads\/temp\/[^\s\)]*\.(png|jpg|jpeg|gif|bmp))/gi,
      (match, path) => {
        const fullUrl = `${API_BASE_URL}/${path}`
        return `<img src="${fullUrl}" alt="图片" style="max-width: 100%; height: auto; margin: 8px 0;" onerror="this.style.display='none'" onload="this.style.display='inline-block'" />`
      }
    )
    
    // 处理图片引用格式：图片X(uploads/temp/xxx.png)
    processedText = processedText.replace(
      /(图片\d+)\s*\((uploads\/temp\/[^\)]*\.(png|jpg|jpeg|gif|bmp))\)/gi,
      (match, imageName, path) => {
        const fullUrl = `${API_BASE_URL}/${path}`
        return `<div style="margin: 12px 0;">
          <strong>${imageName}:</strong><br/>
          <img src="${fullUrl}" alt="${imageName}" title="${imageName}" 
               style="max-width: 100%; height: auto; border: 1px solid #e4e7ed; border-radius: 4px; margin-top: 8px;" 
               onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" 
               onload="this.style.display='block'; this.nextElementSibling.style.display='none';" />
          <div style="display: none; color: #909399; font-size: 12px; margin-top: 4px;">图片加载失败: ${path}</div>
        </div>`
      }
    )
    
    return processedText
    
  } catch (error) {
    console.error('图片路径处理失败:', error)
    return text
  }
}

/**
 * 为HTML内容添加图片样式和错误处理
 * @param {string} htmlContent - HTML内容
 * @returns {string} - 添加样式后的HTML内容
 */
export function enhanceImageDisplay(htmlContent) {
  if (!htmlContent) return htmlContent
  
  try {
    // 为所有img标签添加统一样式和错误处理
    return htmlContent.replace(
      /<img([^>]*?)>/g,
      (match, attributes) => {
        // 检查是否已有错误处理
        if (attributes.includes('onerror')) {
          return match
        }
        
        // 添加默认样式和错误处理
        const defaultStyle = 'max-width: 100%; height: auto; border: 1px solid #e4e7ed; border-radius: 4px; margin: 8px 0;'
        const errorHandler = `onerror="this.style.display='none'; console.warn('图片加载失败:', this.src)"`
        const loadHandler = `onload="this.style.display='block'"`
        
        // 合并样式
        if (attributes.includes('style=')) {
          attributes = attributes.replace(/style="([^"]*)"/, `style="$1 ${defaultStyle}"`)
        } else {
          attributes += ` style="${defaultStyle}"`
        }
        
        return `<img${attributes} ${errorHandler} ${loadHandler}>`
      }
    )
    
  } catch (error) {
    console.error('图片显示增强失败:', error)
    return htmlContent
  }
}

/**
 * 检查图片URL是否可访问
 * @param {string} imageUrl - 图片URL
 * @returns {Promise<boolean>} - 是否可访问
 */
export function checkImageAccessibility(imageUrl) {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve(true)
    img.onerror = () => resolve(false)
    img.src = imageUrl
    
    // 5秒超时
    setTimeout(() => resolve(false), 5000)
  })
}

/**
 * 预加载分析结果中的所有图片
 * @param {string} content - 分析结果内容
 * @returns {Promise<Array>} - 预加载结果
 */
export async function preloadImages(content) {
  if (!content) return []
  
  try {
    // 提取所有图片URL
    const imageUrlRegex = /src="([^"]*uploads\/temp\/[^"]*)"/g
    const imageUrls = []
    let match
    
    while ((match = imageUrlRegex.exec(content)) !== null) {
      const url = match[1].startsWith('http') ? match[1] : `${API_BASE_URL}${match[1].startsWith('/') ? match[1] : '/' + match[1]}`
      imageUrls.push(url)
    }
    
    // 预加载所有图片
    const preloadResults = await Promise.all(
      imageUrls.map(async (url) => {
        const accessible = await checkImageAccessibility(url)
        return { url, accessible }
      })
    )
    
    console.log('图片预加载结果:', preloadResults)
    return preloadResults
    
  } catch (error) {
    console.error('图片预加载失败:', error)
    return []
  }
}

/**
 * 为Vue组件提供的图片处理混入
 */
export const imageProcessingMixin = {
  methods: {
    /**
     * 处理并渲染包含图片的内容
     * @param {string} content - 原始内容
     * @returns {string} - 处理后的HTML内容
     */
    processAndRenderImages(content) {
      const processedContent = processImagePaths(content)
      return enhanceImageDisplay(processedContent)
    },
    
    /**
     * 获取完整的图片URL
     * @param {string} imagePath - 图片路径
     * @returns {string} - 完整URL
     */
    getFullImageUrl(imagePath) {
      if (!imagePath) return ''
      if (imagePath.startsWith('http')) return imagePath
      return `${API_BASE_URL}${imagePath.startsWith('/') ? imagePath : '/' + imagePath}`
    }
  }
}

/**
 * 创建图片查看器
 * @param {string} imageUrl - 图片URL
 * @param {string} title - 图片标题
 */
export async function showImageViewer(imageUrl, title = '图片预览') {
  try {
    // 使用Element Plus的图片预览功能
    const { ElImageViewer } = await import('element-plus')
    
    // 创建预览组件
    const viewer = ElImageViewer({
      urlList: [imageUrl],
      initialIndex: 0,
      onClose: () => {
        viewer.close()
      }
    })
    
    viewer.show()
  } catch (error) {
    console.error('图片查看器创建失败:', error)
    // 简单的fallback：在新窗口打开图片
    window.open(imageUrl, '_blank')
  }
}

export default {
  processImagePaths,
  enhanceImageDisplay,
  checkImageAccessibility,
  preloadImages,
  imageProcessingMixin,
  showImageViewer
} 