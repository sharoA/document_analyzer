// 简单测试图片URL识别和转换功能

// 模拟测试数据
const testContent = `
这是一个测试文档，包含图片链接：

http://localhost:8082/uploads/temp/8552819a-b99b-4475-9358-0142f317fb5e_img_20250620_174702_0.png

页面截图链接：http://localhost:8082/uploads/temp/68a70a95-64d0-4577-9dd1-2dba306865fe_1.png

普通链接：http://example.com/page.html

另一个图片：https://example.com/image.jpg
`

// 图片文件扩展名正则
const imageExtensions = /\.(jpg|jpeg|png|gif|bmp|webp|svg)(\?[^\s]*)?$/i

// 模拟处理函数
function testImageDetection() {
  console.log('=== 图片URL检测测试 ===')
  
  const urls = [
    'http://localhost:8082/uploads/temp/8552819a-b99b-4475-9358-0142f317fb5e_img_20250620_174702_0.png',
    'http://localhost:8082/uploads/temp/68a70a95-64d0-4577-9dd1-2dba306865fe_1.png',
    'https://example.com/image.jpg',
    'https://example.com/image.jpeg',
    'https://example.com/image.gif',
    'https://example.com/page.html',
    'https://example.com/doc.pdf'
  ]
  
  urls.forEach(url => {
    const isImage = imageExtensions.test(url)
    console.log(`${url} -> ${isImage ? '✅ 图片' : '❌ 非图片'}`)
  })
}

// 模拟行处理
function testLineProcessing() {
  console.log('\n=== 行处理测试 ===')
  
  const lines = testContent.split('\n')
  
  lines.forEach((line, index) => {
    const trimmedLine = line.trim()
    const fullUrlMatch = trimmedLine.match(/^(https?:\/\/[^\s]+)$/)
    
    if (fullUrlMatch && imageExtensions.test(fullUrlMatch[1])) {
      console.log(`第${index + 1}行: "${line}" -> ✅ 图片URL`)
    } else if (trimmedLine) {
      console.log(`第${index + 1}行: "${line}" -> ❌ 非图片行`)
    }
  })
}

// 运行测试
testImageDetection()
testLineProcessing()

console.log('\n=== 测试完成 ===')
console.log('如果图片URL能正确识别，说明逻辑没有问题。') 