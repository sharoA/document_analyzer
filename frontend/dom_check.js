// 直接检查前端DOM和Vue状态的调试脚本
// 请在浏览器控制台中运行此脚本

console.clear();
console.log('🔍 直接检查前端DOM和Vue状态');
console.log('=' + '='.repeat(50));

// 1. 检查基本页面状态
console.log('\n1️⃣ 基本页面状态检查');
console.log('   当前URL:', window.location.href);
console.log('   页面标题:', document.title);

// 2. 检查Vue应用状态
console.log('\n2️⃣ Vue应用状态检查');
try {
    const app = document.querySelector('#app').__vue_app__;
    if (app) {
        console.log('   ✅ Vue应用实例存在');
        console.log('   Vue版本:', app.version);
    } else {
        console.log('   ❌ Vue应用实例不存在');
    }
} catch (e) {
    console.log('   ❌ 无法访问Vue应用:', e.message);
}

// 3. 检查当前活跃的标签页
console.log('\n3️⃣ 标签页状态检查');
const tabPanes = document.querySelectorAll('.el-tab-pane');
console.log('   找到的标签页数量:', tabPanes.length);

const activeTab = document.querySelector('.el-tab-pane[style*="display: block"], .el-tab-pane:not([style*="display: none"])');
if (activeTab) {
    console.log('   ✅ 找到活跃标签页');
    const tabId = activeTab.id || activeTab.className;
    console.log('   活跃标签页ID/Class:', tabId);
} else {
    console.log('   ⚠️ 没有明确的活跃标签页');
}

// 4. 检查DesignPlanForm组件相关DOM
console.log('\n4️⃣ DesignPlanForm组件DOM检查');

// 检查表单容器
const formContainer = document.querySelector('.design-plan-form');
console.log('   表单容器(.design-plan-form):', formContainer ? '✅ 存在' : '❌ 不存在');

// 检查服务设计部分
const serviceSection = document.querySelector('h3');
const serviceSections = Array.from(document.querySelectorAll('h3')).filter(h3 => 
    h3.textContent && h3.textContent.includes('服务设计')
);
console.log('   服务设计标题:', serviceSections.length > 0 ? '✅ 找到' : '❌ 未找到');

// 检查服务设计项
const serviceItems = document.querySelectorAll('.service-design-item');
console.log('   服务设计项(.service-design-item)数量:', serviceItems.length);

if (serviceItems.length > 0) {
    console.log('   ✅ 找到服务设计项，数据已加载!');
    serviceItems.forEach((item, i) => {
        const title = item.querySelector('h4');
        console.log(`     服务 ${i+1}:`, title ? title.textContent : '无标题');
    });
} else {
    console.log('   ❌ 没有找到服务设计项');
    
    // 检查是否有"添加服务设计"按钮
    const addButtons = Array.from(document.querySelectorAll('button, .el-button')).filter(btn => 
        btn.textContent && btn.textContent.includes('添加服务设计')
    );
    console.log('   "添加服务设计"按钮:', addButtons.length > 0 ? '✅ 存在' : '❌ 不存在');
    
    if (addButtons.length > 0) {
        console.log('   📍 找到添加按钮，说明组件存在但数据未加载');
    }
}

// 5. 检查API接口项
const apiItems = document.querySelectorAll('.api-item');
console.log('   API接口项(.api-item)数量:', apiItems.length);

// 6. 检查表单输入框
console.log('\n5️⃣ 表单输入框检查');
const allInputs = document.querySelectorAll('input, textarea, select');
console.log('   总输入框数量:', allInputs.length);

const populatedInputs = Array.from(allInputs).filter(input => 
    input.value && input.value.trim() && input.value !== '{}'
);
console.log('   有值的输入框数量:', populatedInputs.length);

if (populatedInputs.length > 0) {
    console.log('   有值的输入框示例:');
    populatedInputs.slice(0, 5).forEach((input, i) => {
        const label = input.placeholder || input.name || input.id || '未知';
        const value = input.value.length > 30 ? input.value.substring(0, 30) + '...' : input.value;
        console.log(`     ${i+1}. ${label}: "${value}"`);
    });
}

// 7. 检查控制台错误
console.log('\n6️⃣ JavaScript错误检查');
console.log('   请检查控制台是否有红色错误信息');

// 8. 检查网络请求
console.log('\n7️⃣ 网络请求检查');
console.log('   请切换到Network标签页，查看是否有以下请求:');
console.log('   - GET /api/file/design-form/f7601b2d-9e60-47bd-8d84-25321d05b62a');

// 9. 手动触发数据加载测试
console.log('\n8️⃣ 手动测试API调用');
const taskId = 'f7601b2d-9e60-47bd-8d84-25321d05b62a';
fetch(`/api/file/design-form/${taskId}`)
    .then(response => response.json())
    .then(data => {
        if (data.success && data.form_data && data.form_data.service_details) {
            const serviceCount = data.form_data.service_details.length;
            console.log('   ✅ API测试成功:', serviceCount, '个服务');
            
            // 检查转换逻辑
            const converted = data.form_data.service_details.map(service => ({
                name: service.service_name,
                apis: service.API设计 ? service.API设计.length : 0
            }));
            console.log('   转换结果:', converted);
            
            // 重新检查DOM（可能数据是异步加载的）
            setTimeout(() => {
                const newServiceItems = document.querySelectorAll('.service-design-item');
                console.log('   🔄 延迟检查服务项数量:', newServiceItems.length);
                
                if (newServiceItems.length > 0) {
                    console.log('   🎉 数据已异步加载到DOM!');
                } else {
                    console.log('   ❌ 数据仍未加载到DOM');
                    console.log('   💡 建议检查Vue DevTools中的组件状态');
                }
            }, 1000);
            
        } else {
            console.log('   ❌ API测试失败，数据结构不正确');
        }
    })
    .catch(error => {
        console.log('   ❌ API测试失败:', error.message);
    });

// 10. 总结和建议
console.log('\n9️⃣ 调试总结');
console.log('=' + '='.repeat(50));
console.log('请检查上述输出，特别关注:');
console.log('1. 是否在正确的标签页上');
console.log('2. .service-design-item 元素数量');
console.log('3. 有值的输入框数量');
console.log('4. 控制台是否有错误信息');
console.log('5. Network请求是否正常');

console.log('\n如果发现问题，请告诉我具体的输出结果!');