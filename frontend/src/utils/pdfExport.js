import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

/**
 * 将HTML元素转换为PDF并下载
 * @param {HTMLElement} element - 要转换的HTML元素
 * @param {string} filename - 下载的文件名
 * @param {Object} options - 配置选项
 */
export async function exportToPDF(element, filename = 'document.pdf', options = {}) {
  const defaultOptions = {
    scale: 2, // 提高图片质量
    useCORS: true,
    allowTaint: true,
    backgroundColor: '#ffffff',
    width: element.scrollWidth,
    height: element.scrollHeight,
    ...options.html2canvas
  }

  const pdfOptions = {
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
    compress: true,
    ...options.jsPDF
  }

  try {
    // 显示加载提示
    const loadingMessage = options.onProgress?.('开始截取页面内容...')

    // 使用html2canvas截取页面
    const canvas = await html2canvas(element, defaultOptions)
    
    options.onProgress?.('正在生成PDF文件...')

    // 计算PDF页面尺寸
    const imgWidth = 210 // A4纸宽度(mm)
    const pageHeight = 295 // A4纸高度(mm)
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    let heightLeft = imgHeight

    // 创建PDF文档
    const pdf = new jsPDF(pdfOptions)
    let position = 0

    // 添加页面内容
    pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight

    // 如果内容超过一页，添加新页面
    while (heightLeft >= 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }

    options.onProgress?.('PDF生成完成，开始下载...')

    // 下载PDF文件
    pdf.save(filename)

    options.onSuccess?.('PDF导出成功')
    return true
  } catch (error) {
    console.error('PDF导出失败:', error)
    options.onError?.(error)
    return false
  }
}

/**
 * 导出分析结果为PDF
 * @param {Object} analysisResult - 分析结果数据
 * @param {string} filename - 文件名
 */
export async function exportAnalysisResultToPDF(analysisResult, filename, options = {}) {
  // 创建临时的HTML内容用于PDF生成
  const tempDiv = document.createElement('div')
  tempDiv.style.cssText = `
    position: absolute;
    top: -9999px;
    left: -9999px;
    width: 800px;
    background: white;
    padding: 40px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #333;
  `

  // 生成PDF内容的HTML
  let htmlContent = `
    <div style="margin-bottom: 30px;">
      <h1 style="color: #409eff; border-bottom: 2px solid #409eff; padding-bottom: 10px; margin-bottom: 20px;">
        文档分析报告
      </h1>
      <div style="color: #666; font-size: 12px;">
        生成时间: ${new Date().toLocaleString()}
      </div>
    </div>
  `

  // 添加基本信息
  if (analysisResult.fileInfo || analysisResult.fileFormat) {
    htmlContent += `
      <div style="margin-bottom: 25px;">
        <h2 style="color: #333; border-left: 4px solid #409eff; padding-left: 10px; margin-bottom: 15px;">
          文件信息
        </h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
    `
    
    const fileInfo = analysisResult.fileInfo || {}
    const fileFormat = analysisResult.fileFormat || {}
    
    if (fileFormat.fileName || fileInfo.name) {
      htmlContent += `<p><strong>文件名:</strong> ${fileFormat.fileName || fileInfo.name}</p>`
    }
    if (fileInfo.type) {
      htmlContent += `<p><strong>文件类型:</strong> ${fileInfo.type}</p>`
    }
    if (fileFormat.subType) {
      htmlContent += `<p><strong>子类型:</strong> ${fileFormat.subType}</p>`
    }
    if (fileInfo.size) {
      htmlContent += `<p><strong>文件大小:</strong> ${formatFileSize(fileInfo.size)}</p>`
    }
    if (analysisResult.details?.length || analysisResult.contentAnalysis?.statistics?.character_count) {
      const charCount = analysisResult.contentAnalysis?.statistics?.character_count || analysisResult.details?.length
      htmlContent += `<p><strong>字符数量:</strong> ${charCount.toLocaleString()}</p>`
    }
    
    htmlContent += `</div></div>`
  }

  // 添加文档结构摘要
  if (analysisResult.documentStructure?.contentSummary) {
    htmlContent += `
      <div style="margin-bottom: 25px;">
        <h2 style="color: #333; border-left: 4px solid #409eff; padding-left: 10px; margin-bottom: 15px;">
          📋 文档结构摘要
        </h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
    `
    
    const summary = analysisResult.documentStructure.contentSummary
    
    if (summary.abstract) {
      htmlContent += `<div style="margin-bottom: 15px;"><strong>文档摘要:</strong><br>${summary.abstract}</div>`
    }
    
    htmlContent += `<div style="margin-bottom: 15px;"><strong>统计信息:</strong></div>`
    htmlContent += `<p>• 功能数量: ${summary.functionCount || 0}</p>`
    htmlContent += `<p>• API数量: ${summary.apiCount || 0}</p>`
    htmlContent += `<p>• 数据库变更: ${summary.dbChangeCount || 0}</p>`
    htmlContent += `<p>• 消息队列: ${summary.mqCount || 0}</p>`
    htmlContent += `<p>• 定时器: ${summary.timerCount || 0}</p>`
    
    if (summary.functionName && summary.functionName.length > 0) {
      htmlContent += `<div style="margin-top: 15px;"><strong>功能列表:</strong><br>`
      summary.functionName.forEach(func => {
        htmlContent += `<span style="display: inline-block; background: #409eff; color: white; padding: 2px 8px; margin: 2px; border-radius: 3px; font-size: 12px;">${func}</span>`
      })
      htmlContent += `</div>`
    }
    
    if (summary.apiName && summary.apiName.length > 0) {
      htmlContent += `<div style="margin-top: 15px;"><strong>API列表:</strong><br>`
      summary.apiName.forEach(api => {
        htmlContent += `<span style="display: inline-block; background: #67c23a; color: white; padding: 2px 8px; margin: 2px; border-radius: 3px; font-size: 12px;">${api}</span>`
      })
      htmlContent += `</div>`
    }
    
    htmlContent += `</div></div>`
  }

  // 添加关键词分析
  if (analysisResult.documentStructure?.contentKeyWord) {
    htmlContent += `
      <div style="margin-bottom: 25px;">
        <h2 style="color: #333; border-left: 4px solid #409eff; padding-left: 10px; margin-bottom: 15px;">
          🔍 关键词分析
        </h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
    `
    
    const keywords = analysisResult.documentStructure.contentKeyWord
    
    if (keywords.keywords && keywords.keywords.length > 0) {
      htmlContent += `<div style="margin-bottom: 15px;"><strong>基础关键词:</strong><br>`
      keywords.keywords.forEach(keyword => {
        htmlContent += `<span style="display: inline-block; background: #909399; color: white; padding: 2px 6px; margin: 2px; border-radius: 3px; font-size: 11px;">${keyword}</span>`
      })
      htmlContent += `</div>`
    }
    
    if (keywords.primaryKeywords && keywords.primaryKeywords.length > 0) {
      htmlContent += `<div style="margin-bottom: 15px;"><strong>主要关键词详情:</strong><br>`
      htmlContent += `<table style="width: 100%; border-collapse: collapse; margin-top: 8px;">`
      htmlContent += `<tr style="background: #f0f0f0;"><th style="border: 1px solid #ddd; padding: 6px; text-align: left;">关键词</th><th style="border: 1px solid #ddd; padding: 6px; text-align: left;">频次</th><th style="border: 1px solid #ddd; padding: 6px; text-align: left;">重要度</th><th style="border: 1px solid #ddd; padding: 6px; text-align: left;">出现位置</th></tr>`
      keywords.primaryKeywords.forEach(kw => {
        const importance = (parseFloat(kw.importance) * 100).toFixed(0)
        const positions = kw.positions ? kw.positions.join(', ') : ''
        htmlContent += `<tr><td style="border: 1px solid #ddd; padding: 6px;">${kw.keyword}</td><td style="border: 1px solid #ddd; padding: 6px;">${kw.frequency}</td><td style="border: 1px solid #ddd; padding: 6px;">${importance}%</td><td style="border: 1px solid #ddd; padding: 6px;">${positions}</td></tr>`
      })
      htmlContent += `</table></div>`
    }
    
    if (keywords.semanticClusters && keywords.semanticClusters.length > 0) {
      htmlContent += `<div style="margin-bottom: 15px;"><strong>语义聚类:</strong><br>`
      keywords.semanticClusters.forEach(cluster => {
        const coherence = (parseFloat(cluster.coherenceScore) * 100).toFixed(0)
        htmlContent += `<div style="margin: 8px 0; padding: 8px; border: 1px solid #e6a23c; border-radius: 4px;">`
        htmlContent += `<div style="font-weight: bold; margin-bottom: 4px;">${cluster.clusterName} (相关度: ${coherence}%)</div>`
        cluster.keywords.forEach(kw => {
          htmlContent += `<span style="display: inline-block; background: #e6a23c; color: white; padding: 2px 6px; margin: 2px; border-radius: 3px; font-size: 11px;">${kw}</span>`
        })
        htmlContent += `</div>`
      })
      htmlContent += `</div>`
    }
    
    htmlContent += `</div></div>`
  }

  // 添加智能内容分析结果
  if (analysisResult.contentAnalysis) {
    htmlContent += `
      <div style="margin-bottom: 25px;">
        <h2 style="color: #333; border-left: 4px solid #409eff; padding-left: 10px; margin-bottom: 15px;">
          📊 智能内容分析结果
        </h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
    `
    
    const contentAnalysis = analysisResult.contentAnalysis
    
    if (contentAnalysis.metadata) {
      htmlContent += `<div style="margin-bottom: 15px;"><strong>分析元数据:</strong><br>`
      htmlContent += `<p>• 分析方法: ${contentAnalysis.metadata.analysis_method}</p>`
      htmlContent += `<p>• 分析耗时: ${(contentAnalysis.metadata.analysis_time || 0).toFixed(2)} 秒</p>`
      htmlContent += `<p>• 内容长度: ${(contentAnalysis.metadata.content_length || 0).toLocaleString()} 字符</p>`
      htmlContent += `<p>• 分析块数: ${contentAnalysis.metadata.chunks_count || 0} 个</p>`
      htmlContent += `</div>`
    }
    
    if (contentAnalysis.change_analysis) {
      htmlContent += `<div style="margin-bottom: 15px;"><strong>🔄 变更分析结果:</strong><br>`
      
      if (contentAnalysis.change_analysis.summary) {
        const summary = contentAnalysis.change_analysis.summary
        htmlContent += `<div style="background: #f0f9ff; padding: 10px; border-radius: 4px; margin-bottom: 10px;">`
        htmlContent += `<strong>分析概览:</strong><br>`
        htmlContent += `<p>• 内容变更: ${summary.total_changes || 0}</p>`
        htmlContent += `<p>• 删除项目: ${summary.total_deletions || 0}</p>`
        htmlContent += `<p>• 总变更数: ${(summary.total_changes || 0) + (summary.total_deletions || 0)}</p>`
        htmlContent += `</div>`
      }
      
      if (contentAnalysis.change_analysis.change_analyses && contentAnalysis.change_analysis.change_analyses.length > 0) {
        htmlContent += `<div style="margin-bottom: 10px;"><strong>变更详情:</strong></div>`
        contentAnalysis.change_analysis.change_analyses.forEach((change, index) => {
          if (change.current_change && change.current_change[0]) {
            const changeInfo = change.current_change[0]
            htmlContent += `<div style="border: 1px solid #ddd; padding: 8px; margin: 6px 0; border-radius: 4px;">`
            htmlContent += `<div style="font-weight: bold;">变更 #${index + 1} - ${changeInfo.changeType || '未知变更'}</div>`
            if (changeInfo.changeReason) {
              htmlContent += `<p><strong>变更原因:</strong> ${changeInfo.changeReason}</p>`
            }
            if (changeInfo.changeItems && changeInfo.changeItems.length > 0) {
              htmlContent += `<div><strong>具体变更:</strong><ul>`
              changeInfo.changeItems.forEach(item => {
                htmlContent += `<li>${item}</li>`
              })
              htmlContent += `</ul></div>`
            }
            htmlContent += `</div>`
          }
        })
      }
      
      if (contentAnalysis.change_analysis.deletion_analyses && contentAnalysis.change_analysis.deletion_analyses.length > 0) {
        htmlContent += `<div style="margin-bottom: 10px;"><strong>🗑️ 删除项分析:</strong></div>`
        contentAnalysis.change_analysis.deletion_analyses.forEach((deletion, index) => {
          htmlContent += `<div style="border: 1px solid #f56c6c; padding: 8px; margin: 6px 0; border-radius: 4px; background: #fef0f0;">`
          htmlContent += `<div style="font-weight: bold;">删除项 #${index + 1}</div>`
          if (deletion.deletedItem) {
            htmlContent += `<p><strong>删除项:</strong> ${deletion.deletedItem}</p>`
          }
          if (deletion.section) {
            htmlContent += `<p><strong>所属章节:</strong> ${deletion.section}</p>`
          }
          if (deletion.analysisResult) {
            htmlContent += `<p><strong>分析结果:</strong> ${deletion.analysisResult}</p>`
          }
          htmlContent += `</div>`
        })
      }
      
      htmlContent += `</div>`
    }
    
    htmlContent += `</div></div>`
  }

  // 添加摘要
  if (analysisResult.analysisSummary) {
    htmlContent += `
      <div style="margin-bottom: 25px;">
        <h2 style="color: #333; border-left: 4px solid #409eff; padding-left: 10px; margin-bottom: 15px;">
          分析摘要
        </h2>
        <div style="background: #f0f9ff; padding: 15px; border-radius: 5px; border-left: 4px solid #409eff;">
          ${analysisResult.analysisSummary.replace(/\n/g, '<br>')}
        </div>
      </div>
    `
  }

  // 添加详细内容
  if (analysisResult.content) {
    htmlContent += `
      <div style="margin-bottom: 25px;">
        <h2 style="color: #333; border-left: 4px solid #409eff; padding-left: 10px; margin-bottom: 15px;">
          文档内容
        </h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; white-space: pre-wrap; max-height: none;">
          ${analysisResult.content.substring(0, 5000)}${analysisResult.content.length > 5000 ? '\n\n... (内容过长，已截取前5000字符)' : ''}
        </div>
      </div>
    `
  }

  // 添加Markdown报告
  if (analysisResult.markdownContent) {
    htmlContent += `
      <div style="margin-bottom: 25px;">
        <h2 style="color: #333; border-left: 4px solid #409eff; padding-left: 10px; margin-bottom: 15px;">
          结构化分析报告
        </h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
          ${convertMarkdownToHTML(analysisResult.markdownContent)}
        </div>
      </div>
    `
  }

  // 添加变更分析
  if (analysisResult.changeAnalysis) {
    htmlContent += `
      <div style="margin-bottom: 25px;">
        <h2 style="color: #333; border-left: 4px solid #409eff; padding-left: 10px; margin-bottom: 15px;">
          变更分析
        </h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
          ${renderChangeAnalysis(analysisResult.changeAnalysis)}
        </div>
      </div>
    `
  }

  tempDiv.innerHTML = htmlContent
  document.body.appendChild(tempDiv)

  try {
    const result = await exportToPDF(tempDiv, filename, options)
    return result
  } finally {
    document.body.removeChild(tempDiv)
  }
}

/**
 * 专门用于导出页面截图为PDF
 * @param {HTMLElement} element - 要截图的页面元素
 * @param {string} filename - 文件名
 * @param {Object} options - 配置选项
 */
export async function exportPageScreenshotToPDF(element, filename = 'page-screenshot.pdf', options = {}) {
  const defaultHtml2CanvasOptions = {
    scale: 1,
    useCORS: true,
    allowTaint: true,
    backgroundColor: '#ffffff',
    scrollX: 0,
    scrollY: 0,
    width: element.offsetWidth || element.clientWidth,
    height: element.offsetHeight || element.clientHeight,
    logging: true,
    imageTimeout: 30000,
    removeContainer: false,
    ignoreElements: function(element) {
      // 忽略可能导致问题的元素
      return element.classList && (
        element.classList.contains('el-loading-mask') ||
        element.classList.contains('el-message') ||
        element.classList.contains('el-notification')
      )
    },
    ...options.html2canvas
  }

  const pdfOptions = {
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
    compress: true,
    ...options.jsPDF
  }

  try {
    options.onProgress?.('正在准备页面截图...')

    // 确保元素完全可见
    const originalStyles = {
      overflow: element.style.overflow,
      maxHeight: element.style.maxHeight,
      height: element.style.height,
      position: element.style.position
    }
    
    element.style.overflow = 'visible'
    element.style.maxHeight = 'none'
    element.style.height = 'auto'
    element.style.position = 'relative'

    // 等待更长时间让页面重新渲染和图片加载
    await new Promise(resolve => setTimeout(resolve, 500))

    options.onProgress?.('开始截取页面内容...')

    // 尝试多次截取，以防第一次失败
    let canvas = null
    let attempts = 0
    const maxAttempts = 3

    while (attempts < maxAttempts && !canvas) {
      try {
        attempts++
        if (attempts > 1) {
          options.onProgress?.(`重试截图中... (${attempts}/${maxAttempts})`)
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
        
        canvas = await html2canvas(element, defaultHtml2CanvasOptions)
        
        // 检查canvas是否有效
        if (canvas && canvas.width > 0 && canvas.height > 0) {
          break
        } else {
          canvas = null
          throw new Error('生成的Canvas无效')
        }
      } catch (error) {
        console.warn(`截图尝试 ${attempts} 失败:`, error)
        if (attempts === maxAttempts) {
          throw error
        }
      }
    }

    if (!canvas) {
      throw new Error('无法生成页面截图')
    }
    
    options.onProgress?.('正在生成PDF文档...')

    // 计算PDF页面尺寸
    const imgWidth = 210 // A4纸宽度(mm)
    const pageHeight = 297 // A4纸高度(mm) - 标准A4
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    
    // 创建PDF文档
    const pdf = new jsPDF(pdfOptions)
    
    if (imgHeight <= pageHeight) {
      // 内容可以放在一页内
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, imgWidth, imgHeight)
    } else {
      // 需要分页
      let heightLeft = imgHeight
      let position = 0
      let pageNum = 1

      // 第一页
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight

      // 添加后续页面
      while (heightLeft >= 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pageNum++
        pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
        
        options.onProgress?.(`正在生成第${pageNum}页...`)
      }
    }

    // 恢复原始样式
    element.style.overflow = originalStyles.overflow
    element.style.maxHeight = originalStyles.maxHeight
    element.style.height = originalStyles.height
    element.style.position = originalStyles.position

    options.onProgress?.('PDF生成完成，开始下载...')

    // 下载PDF文件
    pdf.save(filename)

    options.onSuccess?.('页面PDF导出成功')
    return true
  } catch (error) {
    console.error('页面PDF导出失败:', error)
    options.onError?.(error)
    return false
  }
}

/**
 * 简化版页面PDF导出
 * @param {HTMLElement} element - 要截图的页面元素
 * @param {string} filename - 文件名
 * @param {Object} options - 配置选项
 */
export async function exportSimplePageToPDF(element, filename = 'page.pdf', options = {}) {
  try {
    options.onProgress?.('正在准备页面截图...')
    
    // 使用最基础的html2canvas配置
    const canvas = await html2canvas(element, {
      allowTaint: true,
      useCORS: true,
      backgroundColor: '#ffffff',
      scale: 1,
      logging: false
    })
    
    options.onProgress?.('正在生成PDF...')
    
    // 创建PDF
    const pdf = new jsPDF('p', 'mm', 'a4')
    const imgWidth = 210
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    const pageHeight = 297
    
    if (imgHeight <= pageHeight) {
      // 单页
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, imgWidth, imgHeight)
    } else {
      // 多页
      let position = 0
      let heightLeft = imgHeight
      
      pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
      
      while (heightLeft >= 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }
    }
    
    options.onProgress?.('下载PDF文件...')
    pdf.save(filename)
    
    options.onSuccess?.('PDF导出成功')
    return true
  } catch (error) {
    console.error('简化PDF导出失败:', error)
    options.onError?.(error)
    return false
  }
}

/**
 * 直接从DOM内容生成PDF（不使用截图）
 * @param {HTMLElement} element - 要转换的元素
 * @param {string} filename - 文件名
 * @param {Object} options - 配置选项
 */
export async function exportDOMContentToPDF(element, filename = 'content.pdf', options = {}) {
  try {
    options.onProgress?.('正在提取页面内容...')
    
    // 创建PDF文档
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = 210
    const pageHeight = 297
    const margin = 20
    const contentWidth = pageWidth - (margin * 2)
    
    let currentY = margin
    let pageNumber = 1
    
    // 添加标题
    pdf.setFontSize(18)
    pdf.setFont(undefined, 'bold')
    currentY += 10
    pdf.text('文档分析报告', margin, currentY)
    currentY += 15
    
    // 添加生成时间
    pdf.setFontSize(10)
    pdf.setFont(undefined, 'normal')
    pdf.text(`生成时间: ${new Date().toLocaleString()}`, margin, currentY)
    currentY += 20
    
    options.onProgress?.('正在处理文档内容...')
    
    // 提取所有文本内容
    const textContent = extractTextFromElement(element)
    
    if (textContent.length === 0) {
      pdf.setFontSize(12)
      pdf.text('暂无内容', margin, currentY)
    } else {
      // 分段处理内容
      for (let section of textContent) {
        // 检查是否需要新页面
        if (currentY + 30 > pageHeight - margin) {
          pdf.addPage()
          pageNumber++
          currentY = margin + 10
          options.onProgress?.(`正在生成第${pageNumber}页...`)
        }
        
        // 添加段落标题
        if (section.title) {
          pdf.setFontSize(14)
          pdf.setFont(undefined, 'bold')
          currentY += 8
          pdf.text(section.title, margin, currentY)
          currentY += 10
        }
        
        // 添加段落内容
        if (section.content) {
          pdf.setFontSize(10)
          pdf.setFont(undefined, 'normal')
          
          // 将长文本分行
          const lines = pdf.splitTextToSize(section.content, contentWidth)
          
          for (let line of lines) {
            // 检查是否需要新页面
            if (currentY + 5 > pageHeight - margin) {
              pdf.addPage()
              pageNumber++
              currentY = margin + 10
              options.onProgress?.(`正在生成第${pageNumber}页...`)
            }
            
            pdf.text(line, margin, currentY)
            currentY += 5
          }
          
          currentY += 5 // 段落间距
        }
      }
    }
    
    options.onProgress?.('正在保存PDF文件...')
    
    // 保存PDF
    pdf.save(filename)
    
    options.onSuccess?.('PDF导出成功')
    return true
  } catch (error) {
    console.error('DOM内容PDF导出失败:', error)
    options.onError?.(error)
    return false
  }
}

/**
 * 从DOM元素中提取文本内容
 * @param {HTMLElement} element - 要提取的元素
 */
function extractTextFromElement(element) {
  const sections = []
  
  // 首先尝试找到解析结果容器
  const analysisResult = element.querySelector('.analysis-result') || element.querySelector('.tab-content') || element
  
  // 提取文件基本信息
  const infoCard = analysisResult.querySelector('.info-card')
  if (infoCard) {
    const cardTitle = infoCard.querySelector('h5')
    const cardContent = infoCard.querySelector('.el-descriptions, .el-card__body')
    if (cardTitle && cardContent) {
      sections.push({
        title: cardTitle.textContent.trim(),
        content: extractDescriptionsContent(cardContent)
      })
    }
  }
  
  // 提取所有卡片内容
  const allCards = analysisResult.querySelectorAll('.el-card')
  allCards.forEach(card => {
    const header = card.querySelector('.el-card__header h5, .el-card__header .content-analysis-header h5')
    const body = card.querySelector('.el-card__body')
    
    if (header && body) {
      const title = header.textContent.trim()
      const content = extractCardContent(body)
      
      if (title && content) {
        sections.push({
          title: title,
          content: content
        })
      }
    }
  })
  
  // 如果没有找到卡片，尝试提取其他结构化内容
  if (sections.length === 0) {
    // 提取所有标题和相关内容
    const headings = analysisResult.querySelectorAll('h1, h2, h3, h4, h5, h6')
    headings.forEach(heading => {
      const title = heading.textContent.trim()
      if (title) {
        let content = ''
        let nextElement = heading.nextElementSibling
        
        while (nextElement && !nextElement.matches('h1, h2, h3, h4, h5, h6')) {
          const text = extractElementText(nextElement)
          if (text) {
            content += text + '\n'
          }
          nextElement = nextElement.nextElementSibling
        }
        
        sections.push({
          title: title,
          content: content.trim()
        })
      }
    })
  }
  
  // 最后备选方案：提取所有可见文本
  if (sections.length === 0) {
    const allText = analysisResult.textContent.trim()
    if (allText) {
      const paragraphs = allText.split('\n').filter(p => p.trim().length > 10)
      paragraphs.forEach(p => {
        sections.push({
          title: null,
          content: p.trim()
        })
      })
    }
  }
  
  return sections
}

/**
 * 提取描述列表的内容
 */
function extractDescriptionsContent(element) {
  let content = ''
  
  // 处理 el-descriptions
  const descItems = element.querySelectorAll('.el-descriptions__label, .el-descriptions__content')
  if (descItems.length > 0) {
    for (let i = 0; i < descItems.length; i += 2) {
      const label = descItems[i]?.textContent?.trim()
      const value = descItems[i + 1]?.textContent?.trim()
      if (label && value) {
        content += `${label}: ${value}\n`
      }
    }
  } else {
    // 备选方案：直接提取文本
    content = element.textContent.trim()
  }
  
  return content
}

/**
 * 提取卡片主体内容
 */
function extractCardContent(element) {
  let content = ''
  
  // 处理文档摘要
  const abstractText = element.querySelector('.abstract-text')
  if (abstractText) {
    content += '文档摘要: ' + abstractText.textContent.trim() + '\n\n'
  }
  
  // 处理描述列表
  const descriptions = element.querySelectorAll('.el-descriptions')
  descriptions.forEach(desc => {
    content += extractDescriptionsContent(desc) + '\n'
  })
  
  // 处理功能列表
  const functionTags = element.querySelectorAll('.function-list .el-tag, .api-list .el-tag')
  if (functionTags.length > 0) {
    const tagTexts = Array.from(functionTags).map(tag => tag.textContent.trim()).join(', ')
    content += '相关项目: ' + tagTexts + '\n'
  }
  
  // 处理关键词
  const keywordTags = element.querySelectorAll('.keywords-section .el-tag, .primary-keywords .el-tag')
  if (keywordTags.length > 0) {
    const keywords = Array.from(keywordTags).map(tag => tag.textContent.trim()).join(', ')
    content += '关键词: ' + keywords + '\n'
  }
  
  // 处理表格
  const tables = element.querySelectorAll('.el-table, table')
  tables.forEach(table => {
    const rows = table.querySelectorAll('tr')
    rows.forEach(row => {
      const cells = row.querySelectorAll('th, td')
      if (cells.length > 0) {
        const rowText = Array.from(cells).map(cell => cell.textContent.trim()).join(' | ')
        content += rowText + '\n'
      }
    })
    content += '\n'
  })
  
  // 处理变更分析
  const changeCards = element.querySelectorAll('.change-item-card, .deletion-item-card')
  changeCards.forEach((card, index) => {
    const cardText = extractElementText(card)
    if (cardText) {
      content += `变更项 ${index + 1}: ${cardText}\n`
    }
  })
  
  // 处理语义聚类
  const clusterItems = element.querySelectorAll('.cluster-item')
  clusterItems.forEach(cluster => {
    const clusterText = extractElementText(cluster)
    if (clusterText) {
      content += `聚类: ${clusterText}\n`
    }
  })
  
  // 如果没有找到特定内容，提取所有文本
  if (!content.trim()) {
    content = extractElementText(element)
  }
  
  return content.trim()
}

/**
 * 提取元素的可见文本内容
 */
function extractElementText(element) {
  if (!element) return ''
  
  // 忽略隐藏元素
  if (element.style.display === 'none' || element.hidden) {
    return ''
  }
  
  // 对于包含子元素的元素，递归提取
  let text = ''
  
  if (element.children.length > 0) {
    // 有子元素，递归处理
    Array.from(element.children).forEach(child => {
      const childText = extractElementText(child)
      if (childText) {
        text += childText + ' '
      }
    })
  } else {
    // 叶子节点，直接获取文本
    text = element.textContent?.trim() || ''
  }
  
  return text.trim()
}

// 辅助函数：格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 辅助函数：简单的Markdown转HTML
function convertMarkdownToHTML(markdown) {
  if (!markdown) return ''
  
  return markdown
    .replace(/#{3}\s*(.*?)(?=\n|$)/g, '<h3 style="color: #333; margin: 15px 0 10px 0;">$1</h3>')
    .replace(/#{2}\s*(.*?)(?=\n|$)/g, '<h2 style="color: #333; margin: 20px 0 15px 0;">$1</h2>')
    .replace(/#{1}\s*(.*?)(?=\n|$)/g, '<h1 style="color: #333; margin: 25px 0 20px 0;">$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background: #f1f1f1; padding: 2px 4px; border-radius: 3px;">$1</code>')
    .replace(/^\d+\.\s*(.*?)$/gm, '<li style="margin: 5px 0;">$1</li>')
    .replace(/^[-\*]\s*(.*?)$/gm, '<li style="margin: 5px 0;">$1</li>')
    .replace(/\n/g, '<br>')
}

// 辅助函数：渲染变更分析
function renderChangeAnalysis(changeAnalysis) {
  if (!changeAnalysis) return ''
  
  let html = ''
  
  if (changeAnalysis.summary) {
    html += `<div style="margin-bottom: 15px;"><strong>变更摘要:</strong><br>${changeAnalysis.summary}</div>`
  }
  
  if (changeAnalysis.changes && Array.isArray(changeAnalysis.changes)) {
    html += '<div><strong>详细变更:</strong><ul style="margin: 10px 0; padding-left: 20px;">'
    changeAnalysis.changes.forEach(change => {
      const typeColor = getChangeTypeColor(change.type)
      html += `<li style="margin: 8px 0;"><span style="color: ${typeColor}; font-weight: bold;">[${change.type}]</span> ${change.description || change.content}</li>`
    })
    html += '</ul></div>'
  }
  
  return html
}

// 辅助函数：获取变更类型颜色
function getChangeTypeColor(changeType) {
  const colorMap = {
    '新增': '#67c23a',
    '修改': '#e6a23c',
    '删除': '#f56c6c',
    '相同': '#909399'
  }
  return colorMap[changeType] || '#333'
} 