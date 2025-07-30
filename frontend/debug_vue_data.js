// 在浏览器控制台运行这个调试脚本，检查Vue数据状态

console.clear();
console.log('🔍 检查Vue组件数据状态');

// 1. 手动触发API调用和数据转换
const taskId = 'f7601b2d-9e60-47bd-8d84-25321d05b62a';

fetch(`/api/file/design-form/${taskId}`)
  .then(response => response.json())
  .then(data => {
    console.log('📡 API响应数据:', data);
    
    // 2. 检查是否为分析结果格式
    const isAnalysisResult = data.ai_analysis || data.content_analysis || data.document_parsing;
    console.log('🔍 是否为分析结果格式:', isAnalysisResult ? '是' : '否');
    
    if (isAnalysisResult) {
      console.log('🔄 开始手动转换分析结果数据...');
      
      // 手动执行转换逻辑（简化版）
      const docParsing = data.document_parsing?.data || {};
      const contentSummary = docParsing.documentStructure?.contentSummary || {};
      const contentAnalysis = data.content_analysis?.data || {};
      const changeAnalyses = contentAnalysis.change_analysis?.change_analyses || [];
      
      console.log('📊 提取的关键数据:');
      console.log('  - 文件名:', docParsing.fileFormat?.fileName);
      console.log('  - API数量:', contentSummary.apiName?.length || 0);
      console.log('  - 变更分析数量:', changeAnalyses.length);
      console.log('  - 功能名称:', contentSummary.functionName);
      
      // 生成服务设计
      const apiNames = contentSummary.apiName || [];
      const serviceDesigns = [];
      
      if (apiNames.length > 0) {
        apiNames.forEach((apiName, index) => {
          const relatedChange = changeAnalyses[index] || changeAnalyses[0];
          
          serviceDesigns.push({
            service_name: `${apiName}服务`,
            service_english_name: `${apiName.replace(/[^a-zA-Z0-9]/g, '').toLowerCase()}-service`,
            service_duty: relatedChange?.changeReason || '核心业务逻辑处理',
            core_modules: relatedChange?.changeItems?.slice(0, 3).join('\n- ') || '- 核心模块',
            apis: [{
              interface_type: relatedChange?.changeType === '新增' ? '新增' : '查询',
              uri: `/api/${apiName.replace(/[^a-zA-Z0-9]/g, '').toLowerCase()}`,
              method: relatedChange?.changeType === '新增' ? 'POST' : 'GET',
              description: apiName,
              request_params: '{"param": "value"}',
              response_params: '{"success": true}',
              special_requirements: '需要权限验证'
            }]
          });
        });
      } else {
        // 默认服务设计
        changeAnalyses.slice(0, 2).forEach((change, index) => {
          serviceDesigns.push({
            service_name: change.changeType === '新增' ? '额度管理服务' : '接口服务',
            service_english_name: `service-${index + 1}`,
            service_duty: change.changeReason || '核心业务逻辑处理',
            core_modules: change.changeItems?.slice(0, 3).join('\n- ') || '- 核心模块',
            apis: [{
              interface_type: change.changeType || '查询',
              uri: `/api/service${index + 1}`,
              method: change.changeType === '新增' ? 'POST' : 'GET',
              description: change.changeItems?.[0] || '业务接口',
              request_params: '{"param": "value"}',
              response_params: '{"success": true}',
              special_requirements: '需要权限验证'
            }]
          });
        });
      }
      
      console.log('🎯 生成的服务设计:', serviceDesigns);
      
      // 3. 检查当前DOM中的输入框
      setTimeout(() => {
        console.log('\n📝 检查当前输入框状态:');
        
        // 查找服务职责输入框
        const serviceInputs = document.querySelectorAll('input[placeholder*="服务职责"], input[placeholder*="职责"]');
        console.log('找到的服务职责输入框数量:', serviceInputs.length);
        
        serviceInputs.forEach((input, i) => {
          console.log(`输入框 ${i + 1}:`, {
            placeholder: input.placeholder,
            value: input.value,
            id: input.id
          });
        });
        
        // 查看所有输入框的值
        const allInputs = document.querySelectorAll('input, textarea');
        const hasValue = Array.from(allInputs).filter(inp => inp.value && inp.value.trim());
        console.log('有值的输入框总数:', hasValue.length);
        
        if (hasValue.length > 0) {
          console.log('有值的输入框示例:');
          hasValue.slice(0, 5).forEach(inp => {
            console.log(`  - ${inp.placeholder}: "${inp.value.substring(0, 30)}..."`);
          });
        }
        
        // 4. 检查Vue组件状态
        console.log('\n🔍 Vue组件状态检查:');
        try {
          // 尝试获取Vue实例
          const vueApp = document.querySelector('#app').__vue_app__;
          if (vueApp) {
            console.log('Vue应用存在');
            // 这里我们无法直接访问组件实例，但可以建议检查Vue DevTools
          }
        } catch (e) {
          console.log('无法访问Vue实例');
        }
        
        console.log('\n💡 下一步建议:');
        console.log('1. 检查Vue DevTools中DesignPlanForm组件的formData.service_designs');
        console.log('2. 确认loadFormData函数是否被正确调用');
        console.log('3. 检查updateFormDataReactively函数是否正确执行');
        console.log('4. 查看控制台是否有Vue相关的错误信息');
        
      }, 1000);
      
    } else {
      console.log('❌ API返回的不是分析结果格式');
    }
  })
  .catch(error => {
    console.error('❌ API调用失败:', error);
  });

console.log('🔧 调试脚本已启动，请等待结果...');