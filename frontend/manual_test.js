// 在浏览器控制台中粘贴并运行此代码
// 手动测试数据加载和显示

console.clear();
console.log('🔧 手动测试前端数据加载...');

const taskId = 'f7601b2d-9e60-47bd-8d84-25321d05b62a';

// 1. 直接调用API获取数据
fetch(`/api/file/design-form/${taskId}`)
  .then(response => response.json())
  .then(data => {
    console.log('✅ API数据获取成功:', data);
    
    if (data.success && data.form_data && data.form_data.service_details) {
      const serviceDetails = data.form_data.service_details;
      console.log('📊 服务详情数量:', serviceDetails.length);
      
      // 2. 手动执行数据转换逻辑（模拟convertBackendDataToFormData）
      const convertedServices = serviceDetails.map((service, index) => {
        console.log(`🔄 转换第${index + 1}个服务:`, service.service_name);
        
        // 处理API设计数据
        let apis = [];
        if (service.API设计 && Array.isArray(service.API设计)) {
          console.log(`  发现API设计数组，长度: ${service.API设计.length}`);
          apis = service.API设计.map((apiItem, apiIndex) => {
            console.log(`    API ${apiIndex + 1}:`, apiItem);
            return {
              interface_type: apiItem.interface_type || '查询',
              uri: apiItem.uri || '',
              method: apiItem.method || 'GET',
              description: apiItem.description || '',
              request_params: apiItem.request_params || '{}',
              response_params: apiItem.response_params || '{}',
              special_requirements: apiItem.special_requirements || ''
            };
          });
        }
        
        const convertedService = {
          service_name: service.service_name || '',
          service_english_name: service.service_english_name || '',
          service_duty: service.service_duty || '',
          core_modules: service.core_modules || '',
          apis: apis,
          data_table_sql: service.API设计 && service.API设计[0] ? service.API设计[0].data_table_sql || '' : '',
          dependence_service: service.API设计 && service.API设计[0] && service.API设计[0].dependence_service ? 
            (Array.isArray(service.API设计[0].dependence_service) ? service.API设计[0].dependence_service.join(', ') : service.API设计[0].dependence_service) : ''
        };
        
        console.log(`✅ 第${index + 1}个服务转换完成:`, convertedService);
        return convertedService;
      });
      
      console.log('🎯 转换完成，共', convertedServices.length, '个服务:', convertedServices);
      
      // 3. 检查转换后的数据结构
      convertedServices.forEach((service, i) => {
        console.log(`\n📋 服务 ${i+1}: ${service.service_name}`);
        console.log(`  英文名: ${service.service_english_name}`);
        console.log(`  职责: ${service.service_duty}`);
        console.log(`  APIs: ${service.apis.length} 个`);
        
        service.apis.forEach((api, j) => {
          console.log(`    API ${j+1}: ${api.interface_type} ${api.method} ${api.uri} - ${api.description}`);
        });
      });
      
      // 4. 尝试直接操作DOM（如果数据没有通过Vue正确显示）
      console.log('\n🔧 尝试直接验证DOM状态...');
      
      // 检查是否有"添加服务设计"按钮
      const addButtons = document.querySelectorAll('el-button');
      const addServiceButton = Array.from(addButtons).find(btn => 
        btn.textContent && btn.textContent.includes('添加服务设计')
      );
      
      if (addServiceButton) {
        console.log('✅ 找到"添加服务设计"按钮');
        
        // 检查是否已经有服务设计项
        const serviceItems = document.querySelectorAll('.service-design-item');
        console.log(`📊 当前DOM中的服务设计项: ${serviceItems.length} 个`);
        
        if (serviceItems.length === 0) {
          console.log('❌ DOM中没有服务设计项，说明数据没有正确加载到Vue组件');
          console.log('💡 可能的原因:');
          console.log('  1. props.taskId 没有正确传递');
          console.log('  2. loadFormData 函数没有被调用');
          console.log('  3. convertBackendDataToFormData 函数有问题');
          console.log('  4. updateFormDataReactively 函数没有正确更新数据');
          console.log('  5. Vue的响应式系统没有正确工作');
          
          // 尝试查看Vue组件状态（如果可能）
          console.log('\n🔍 建议在Vue DevTools中检查:');
          console.log('  - DesignPlanForm组件的props.taskId');
          console.log('  - formData.value.service_designs数组');
          console.log('  - 组件的生命周期是否正确执行');
        } else {
          console.log('✅ DOM中有服务设计项，数据已加载');
        }
      } else {
        console.log('❌ 没有找到"添加服务设计"按钮，可能页面状态不对');
      }
      
    } else {
      console.log('❌ API返回的数据结构不正确');
    }
  })
  .catch(error => {
    console.error('❌ API调用失败:', error);
  });

console.log('🔧 手动测试脚本执行完成，请查看上述日志');

// 额外建议
console.log('\n💡 调试建议:');
console.log('1. 检查浏览器Network标签页是否有API请求');
console.log('2. 检查Vue DevTools中DesignPlanForm组件的数据状态');
console.log('3. 在控制台中输入: document.querySelector("#app").__vue_app__');
console.log('4. 查看Console中是否有JavaScript错误');