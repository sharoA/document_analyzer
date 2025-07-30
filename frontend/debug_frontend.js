// 在浏览器控制台运行这个脚本来调试
console.clear();
console.log('🔍 调试前端数据加载问题...');

// 1. 检查当前taskId
const getCurrentTaskId = () => {
    // 从多个可能的地方获取taskId
    const urlParams = new URLSearchParams(window.location.search);
    const taskIdFromUrl = urlParams.get('taskId');
    
    // 从Vue应用状态获取
    let taskIdFromVue = null;
    try {
        const app = document.querySelector('#app').__vue_app__;
        if (app && app._instance) {
            // 尝试从Vue实例获取taskId
            taskIdFromVue = 'f7601b2d-9e60-47bd-8d84-25321d05b62a'; // 从控制台看到的
        }
    } catch (e) {
        console.log('无法从Vue获取taskId');
    }
    
    console.log('📍 URL中的taskId:', taskIdFromUrl);
    console.log('📍 Vue中的taskId:', taskIdFromVue);
    
    return taskIdFromVue || taskIdFromUrl || 'f7601b2d-9e60-47bd-8d84-25321d05b62a';
};

const taskId = getCurrentTaskId();
console.log('🆔 使用的taskId:', taskId);

// 2. 测试API调用（通过Vite代理）
console.log('🚀 测试前端API调用（通过Vite代理）...');
const apiUrl = `/api/file/design-form/${taskId}`;
console.log('📡 请求URL:', apiUrl);

fetch(apiUrl)
    .then(response => {
        console.log('📡 响应状态:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('📄 API响应数据:', data);
        
        if (data.success && data.form_data) {
            const serviceDetails = data.form_data.service_details || [];
            console.log('✅ 找到服务详情:', serviceDetails.length, '个服务');
            
            serviceDetails.forEach((service, i) => {
                console.log(`服务 ${i+1}: ${service.service_name}`);
                const apis = service.API设计 || [];
                console.log(`  - API数量: ${apis.length}`);
                apis.forEach((api, j) => {
                    console.log(`    API ${j+1}: ${api.interface_type} ${api.method} ${api.uri}`);
                });
            });
            
            // 3. 检查DOM中是否有服务设计相关元素
            console.log('🔍 检查DOM元素...');
            const serviceItems = document.querySelectorAll('.service-design-item');
            console.log('找到的服务设计项:', serviceItems.length);
            
            const addServiceBtn = document.querySelector('el-button');
            console.log('找到的按钮元素:', addServiceBtn ? '存在' : '不存在');
            
            // 4. 检查表单数据是否已加载
            const inputs = document.querySelectorAll('input, textarea');
            const populatedInputs = Array.from(inputs).filter(inp => inp.value && inp.value.trim());
            console.log('有值的输入框数量:', populatedInputs.length);
            
            if (populatedInputs.length > 0) {
                console.log('有值的输入框示例:');
                populatedInputs.slice(0, 3).forEach(inp => {
                    console.log(`  - ${inp.placeholder || inp.type}: "${inp.value.substring(0, 30)}..."`);
                });
            }
            
            // 5. 给出诊断结果
            if (serviceItems.length === 0 && populatedInputs.length === 0) {
                console.log('❌ 诊断结果: 数据没有加载到前端表单');
                console.log('💡 可能原因:');
                console.log('  1. Vue组件的数据绑定有问题');
                console.log('  2. convertBackendDataToFormData函数没有正确执行');
                console.log('  3. formData.value没有正确更新');
                console.log('  4. taskId没有正确传递给组件');
            } else {
                console.log('✅ 数据似乎已经加载到前端');
            }
            
        } else {
            console.log('❌ API返回的数据结构不正确');
        }
    })
    .catch(error => {
        console.error('❌ API调用失败:', error);
    });

console.log('🔍 调试脚本执行完成');