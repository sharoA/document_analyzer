// 在浏览器控制台中运行的调试脚本
// 检查当前页面的数据加载状态

console.clear();
console.log('🔍 开始调试前端数据加载问题...');

// 1. 检查Vue应用实例
const app = document.querySelector('#app').__vue_app__;
if (app) {
    console.log('✅ Vue应用实例存在');
} else {
    console.log('❌ Vue应用实例不存在');
}

// 2. 检查当前页面URL和参数
console.log('🔗 当前页面URL:', window.location.href);
console.log('🔗 URL参数:', new URLSearchParams(window.location.search).toString());

// 3. 尝试获取任务ID
const urlParams = new URLSearchParams(window.location.search);
const taskId = urlParams.get('taskId') || 'f7601b2d-9e60-47bd-8d84-25321d05b62a';
console.log('🆔 使用的任务ID:', taskId);

// 4. 手动测试API调用
console.log('🚀 手动测试API调用...');
fetch(`/api/file/design-form/${taskId}`)
    .then(response => {
        console.log('📡 API响应状态:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('📄 API响应数据:', data);
        
        if (data.success && data.form_data && data.form_data.service_details) {
            console.log('✅ API数据正确');
            console.log('📊 服务数量:', data.form_data.service_details.length);
            
            data.form_data.service_details.forEach((service, index) => {
                console.log(`服务 ${index + 1}:`, service.service_name);
                console.log(`  APIs:`, service.API设计?.length || 0);
            });
            
            // 5. 测试数据转换逻辑
            console.log('🔄 测试数据转换...');
            const convertedServices = data.form_data.service_details.map(service => {
                const apis = service.API设计?.map(api => ({
                    interface_type: api.interface_type || '查询',
                    uri: api.uri || '',
                    method: api.method || 'GET',
                    description: api.description || '',
                    request_params: api.request_params || '{}',
                    response_params: api.response_params || '{}',
                    special_requirements: api.special_requirements || ''
                })) || [];
                
                return {
                    service_name: service.service_name || '',
                    service_english_name: service.service_english_name || '',
                    service_duty: service.service_duty || '',
                    core_modules: service.core_modules || '',
                    apis: apis
                };
            });
            
            console.log('✅ 转换后的服务数据:', convertedServices);
            
            if (convertedServices.length > 0 && convertedServices[0].apis.length > 0) {
                console.log('🎉 数据转换成功，应该能显示在表单中');
                
                // 6. 检查DOM元素
                const serviceDesignItems = document.querySelectorAll('.service-design-item');
                console.log('🏷️ 找到的服务设计DOM元素:', serviceDesignItems.length);
                
                if (serviceDesignItems.length === 0) {
                    console.log('❌ 页面中没有找到服务设计元素，可能数据没有正确更新到Vue组件');
                    
                    // 7. 尝试查找表单数据
                    const formElements = document.querySelectorAll('input, textarea, select');
                    console.log('📝 页面中的表单元素数量:', formElements.length);
                    
                    // 查找有值的表单元素
                    const populatedElements = Array.from(formElements).filter(el => el.value.trim());
                    console.log('📝 有值的表单元素数量:', populatedElements.length);
                    
                    if (populatedElements.length > 0) {
                        console.log('📝 有值的表单元素示例:');
                        populatedElements.slice(0, 5).forEach((el, i) => {
                            console.log(`  ${i + 1}: ${el.tagName} = "${el.value.substring(0, 50)}..."`);
                        });
                    }
                } else {
                    console.log('✅ 找到了服务设计DOM元素');
                }
            } else {
                console.log('❌ 数据转换后没有有效的API数据');
            }
        } else {
            console.log('❌ API数据结构不正确');
        }
    })
    .catch(error => {
        console.error('❌ API调用失败:', error);
    });

// 8. 检查Vue开发者工具
console.log('💡 建议: 如果有Vue DevTools，请检查组件状态中的formData.service_designs');

console.log('🔍 调试脚本执行完成，请查看上述日志信息');