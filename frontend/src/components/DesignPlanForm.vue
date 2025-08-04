<template>
  <div class="design-plan-form">
    <!-- 加载中状态 -->
    <div v-if="isLoading" class="loading-container">
      <el-icon class="is-loading" size="32"><Loading /></el-icon>
      <p>正在加载表单数据...</p>
    </div>
    
    <!-- 表单内容 -->
    <el-form v-else :model="formData" label-width="120px" class="design-form">
      <!-- 文档标题 -->
      <div class="form-section">
        <h3>设计文档基本信息</h3>
        <el-form-item label="项目名称">
          <el-input v-model="formData.project_name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="版本号">
          <el-input v-model="formData.version" placeholder="请输入版本号" />
        </el-form-item>
      </div>

      <!-- 1. 系统架构设计 -->
      <div class="form-section">
        <h3>1. 系统架构设计</h3>
        
        <!-- 1.1 项目介绍 -->
        <div class="subsection">
          <h4>1.1 项目介绍</h4>
          <el-form-item label="项目背景">
            <el-input 
              v-model="formData.project_intro.background" 
              type="textarea" 
              :rows="8"
              placeholder="请描述项目背景和问题"
            />
          </el-form-item>
        </div>

        <!-- 1.2 功能需求说明 -->
        <div class="subsection">
          <h4>1.2 功能需求说明</h4>
          <div v-for="(requirement, index) in formData.function_requirements" :key="index" class="requirement-item">
            <div class="requirement-header">
              <h5>1.2.{{ index + 1 }} {{ requirement.name }}</h5>
              <!-- <el-button type="danger" size="small" @click="removeRequirement(index)">删除</el-button> -->
            </div>
            
            <el-form-item label="功能名称">
              <el-input v-model="requirement.name" placeholder="请输入功能名称" />
            </el-form-item>
            
            <el-form-item label="调整说明">
              <el-input 
                v-model="requirement.adjust_info" 
                type="textarea" 
                :rows="4"
                placeholder="请输入调整说明"
              />
            </el-form-item>

            <!-- 筛选字段 -->
            <el-form-item label="筛选字段" v-if="requirement.filter_fields">
              <div v-for="(field, fieldIndex) in requirement.filter_fields" :key="fieldIndex" class="field-item">
                <el-row :gutter="10">
                  <el-col :span="4">
                    <el-input v-model="field.name" placeholder="字段名" />
                  </el-col>
                  <el-col :span="4">
                    <el-input v-model="field.type" placeholder="类型格式" />
                  </el-col>
                  <el-col :span="3">
                    <el-input v-model="field.length" placeholder="长度" />
                  </el-col>
                  <el-col :span="3">
                    <el-input v-model="field.default_value" placeholder="默认值" />
                  </el-col>
                  <el-col :span="3">
                    <el-select v-model="field.required" placeholder="必填">
                      <el-option label="是" value="是" />
                      <el-option label="否" value="否" />
                    </el-select>
                  </el-col>
                  <el-col :span="5">
                    <el-input v-model="field.rules" placeholder="规则" />
                  </el-col>
                  <el-col :span="2">
                    <!-- <el-button type="danger" size="small" @click="removeField(requirement.filter_fields, fieldIndex)">删除</el-button> -->
                  </el-col>
                </el-row>
              </div>
              <!-- <el-button type="primary" size="small" @click="addField(requirement, 'filter_fields')">添加筛选字段</el-button> -->
            </el-form-item>

            <!-- 列表字段 -->
            <el-form-item label="列表字段" v-if="requirement.list_fields">
              <div v-for="(field, fieldIndex) in requirement.list_fields" :key="fieldIndex" class="field-item">
                <el-row :gutter="10">
                  <el-col :span="6">
                    <el-input v-model="field.name" placeholder="字段名" />
                  </el-col>
                  <el-col :span="6">
                    <el-input v-model="field.type" placeholder="类型格式" />
                  </el-col>
                  <el-col :span="8">
                    <el-input v-model="field.rules" placeholder="规则" />
                  </el-col>
                  <el-col :span="4">
                    <!-- <el-button type="danger" size="small" @click="removeField(requirement.list_fields, fieldIndex)">删除</el-button> -->
                  </el-col>
                </el-row>
              </div>
              <!-- <el-button type="primary" size="small" @click="addField(requirement, 'list_fields')">添加列表字段</el-button> -->
            </el-form-item>

            <el-form-item label="备注">
              <el-input 
                v-model="requirement.remarks" 
                type="textarea" 
                :rows="2"
                placeholder="备注或特殊要求"
              />
            </el-form-item>
          </div>
          
          <!-- <el-button type="primary" @click="addRequirement">添加功能需求</el-button> -->
        </div>

        <!-- 1.3 总体架构 -->
        <div class="subsection">
          <h4>1.3 总体架构</h4>
          <el-form-item label="架构描述">
            <el-input 
              v-model="formData.project_architecture" 
              type="textarea" 
              :rows="3"
              placeholder="请描述总体架构"
            />
          </el-form-item>
          
          <el-form-item label="服务数量">
            <el-input-number v-model="formData.service_numbers" :min="1" />
          </el-form-item>

          <!-- 服务信息 -->
          <div v-for="(service, index) in formData.services" :key="index" class="service-item">
            <h5>服务 {{ index + 1 }}</h5>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-input v-model="service.service_name" placeholder="服务中文名" />
              </el-col>
              <el-col :span="10">
                <el-input v-model="service.service_english_name" placeholder="服务英文名" />
              </el-col>
              <el-col :span="4">
                <!-- <el-button type="danger" size="small" @click="removeService(index)">删除</el-button> -->
              </el-col>
            </el-row>
          </div>
          <!-- <el-button type="primary" size="small" @click="addService">添加服务</el-button> -->

          <el-form-item label="数据库数量">
            <el-input-number v-model="formData.data_resources" :min="1" />
          </el-form-item>

          <!-- 数据库信息 -->
          <div v-for="(db, index) in formData.databases" :key="index" class="database-item">
            <h5>数据库 {{ index + 1 }}</h5>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-select v-model="db.data_type" placeholder="数据库类型">
                  <el-option label="MySQL" value="mysql" />
                  <el-option label="Redis" value="redis" />
                  <el-option label="MongoDB" value="mongodb" />
                </el-select>
              </el-col>
              <el-col :span="12">
                <el-input v-model="db.description" placeholder="数据库描述" />
              </el-col>
              <el-col :span="4">
                <!-- <el-button type="danger" size="small" @click="removeDatabase(index)">删除</el-button> -->
              </el-col>
            </el-row>
          </div>
          <!-- <el-button type="primary" size="small" @click="addDatabase">添加数据库</el-button> -->
        </div>

        <!-- 1.4 技术栈选型 -->
        <div class="subsection">
          <h4>1.4 技术栈选型</h4>
          <el-form-item label="技术栈">
            <el-input 
              v-model="formData.technology" 
              type="textarea" 
              :rows="6"
              placeholder="请输入技术栈信息，每行一个技术点"
            />
          </el-form-item>
        </div>
      </div>

      <!-- 2. 服务设计 -->
      <div class="form-section">
        <h3>2. 服务设计</h3>
        <div v-for="(service, serviceIndex) in formData.service_designs" :key="serviceIndex" class="service-design-item">
          <div class="service-design-header">
            <h4>2.{{ serviceIndex + 1 }} {{ service.service_name }} ({{ service.service_english_name }})</h4>
            <!-- <el-button type="danger" size="small" @click="removeServiceDesign(serviceIndex)">删除服务</el-button> -->
          </div>

          <el-form-item label="服务职责">
            <el-input v-model="service.service_duty" placeholder="请输入服务职责" />
          </el-form-item>

          <el-form-item label="核心模块">
            <el-input 
              v-model="service.core_modules" 
              type="textarea" 
              :rows="3"
              placeholder="请输入核心模块，每行一个模块"
            />
          </el-form-item>

          <!-- API设计 -->
          <div class="api-design">
            <h5>API设计</h5>
            <div v-for="(api, apiIndex) in service.apis" :key="apiIndex" class="api-item">
              <div class="api-header">
                <h6>接口 {{ apiIndex + 1 }}</h6>
                <!-- <el-button type="danger" size="small" @click="removeApi(service.apis, apiIndex)">删除接口</el-button> -->
              </div>

              <el-row :gutter="10">
                <el-col :span="6">
                  <el-form-item label="接口类型">
                    <el-select v-model="api.interface_type" placeholder="接口类型" clearable>
                      <el-option label="新增" value="新增" />
                      <el-option label="修改" value="修改" />
                      <el-option label="删除" value="删除" />
                    </el-select>
                    <!-- 调试信息 -->
                    <div style="font-size: 12px; color: #999; margin-top: 4px;">
                      当前值: {{ api.interface_type || '空' }}
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="请求方法">
                    <el-select v-model="api.method" placeholder="请求方法" clearable>
                      <el-option label="GET" value="GET" />
                      <el-option label="POST" value="POST" />
                      <el-option label="PUT" value="PUT" />
                      <el-option label="DELETE" value="DELETE" />
                    </el-select>
                    <!-- 调试信息 -->
                    <div style="font-size: 12px; color: #999; margin-top: 4px;">
                      当前值: {{ api.method || '空' }}
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="URI">
                    <el-input v-model="api.uri" placeholder="请输入接口URI" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="接口描述">
                <el-input v-model="api.description" placeholder="请输入接口描述" />
              </el-form-item>

              <el-form-item label="入参示例">
                <el-input 
                  v-model="api.request_params" 
                  type="textarea" 
                  :rows="4"
                  placeholder="请输入入参JSON示例"
                />
              </el-form-item>

              <el-form-item label="返参示例">
                <el-input 
                  v-model="api.response_params" 
                  type="textarea" 
                  :rows="4"
                  placeholder="请输入返参JSON示例"
                />
              </el-form-item>

              <el-form-item label="特殊要求">
                <el-input 
                  v-model="api.special_requirements" 
                  type="textarea" 
                  :rows="2"
                  placeholder="请输入特殊要求"
                />
              </el-form-item>
            </div>
            <!-- <el-button type="primary" size="small" @click="addApi(service)">添加接口</el-button> -->
          </div>

          <el-form-item label="数据库表SQL">
            <el-input 
              v-model="service.data_table_sql" 
              type="textarea" 
              :rows="8"
              placeholder="请输入CREATE TABLE语句"
            />
          </el-form-item>

          <el-form-item label="依赖服务">
            <el-input 
              v-model="service.dependence_service" 
              placeholder="请输入依赖的服务名称，多个用逗号分隔"
            />
          </el-form-item>
        </div>
        <!-- <el-button type="primary" @click="addServiceDesign">添加服务设计</el-button> -->
      </div>

      <!-- 3. 执行要求 -->
      <div class="form-section">
        <h3>3. 执行要求</h3>
        
        <!-- 3.1 涉及服务范围 -->
        <div class="subsection">
          <h4>3.1 涉及服务范围</h4>
          <el-form-item label="服务范围说明">
            <el-input v-model="formData.execution.service_scope" placeholder="如：本次没有新增服务，服务范围为：" />
          </el-form-item>
          
          <div v-for="(service, index) in formData.execution.services" :key="index" class="execution-service-item">
            <el-row :gutter="10">
              <el-col :span="6">
                <el-input v-model="service.service_name" placeholder="服务名称" />
              </el-col>
              <el-col :span="6">
                <el-input v-model="service.service_english_name" placeholder="服务英文名" />
              </el-col>
              <el-col :span="8">
                <el-input v-model="service.gitlab" placeholder="Git地址" />
              </el-col>
              <el-col :span="4">
                <!-- <el-button type="danger" size="small" @click="removeExecutionService(index)">删除</el-button> -->
              </el-col>
            </el-row>
          </div>
          <!-- <el-button type="primary" size="small" @click="addExecutionService">添加服务</el-button> -->
        </div>

        <!-- 3.2 涉及数据库范围 -->
        <div class="subsection">
          <h4>3.2 涉及数据库范围</h4>
          <el-form-item label="数据库范围说明">
            <el-input v-model="formData.execution.data_scope" placeholder="如：本次没有新增数据库" />
          </el-form-item>

          <!-- 数据库配置 -->
          <div v-for="(db, index) in formData.execution.databases" :key="index" class="execution-db-item">
            <h5>数据库配置 {{ index + 1 }}</h5>
            <el-row :gutter="10">
              <el-col :span="4">
                <el-form-item label="类型">
                  <el-select v-model="db.data_type" placeholder="数据库类型">
                    <el-option label="MySQL" value="mysql" />
                    <el-option label="Redis" value="redis" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="16">
                <el-form-item label="连接配置">
                  <el-input 
                    v-model="db.config" 
                    type="textarea" 
                    :rows="3"
                    placeholder="请输入数据库连接配置"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="4">
                <!-- <el-button type="danger" size="small" @click="removeExecutionDatabase(index)">删除</el-button> -->
              </el-col>
            </el-row>
          </div>
          <!-- <el-button type="primary" size="small" @click="addExecutionDatabase">添加数据库配置</el-button> -->
        </div>

        <!-- 3.3 涉及接口范围 -->
        <div class="subsection">
          <h4>3.3 涉及接口范围</h4>
          <el-form-item label="接口范围说明">
            <el-input 
              v-model="formData.execution.scope_interface" 
              type="textarea" 
              :rows="2"
              placeholder="如：本次新增接口，已经按服务范围进行划分，详见设计文档2服务设计部分。"
            />
          </el-form-item>
        </div>
      </div>

      <!-- 表单操作按钮 -->
      <div class="form-actions">
        <el-button type="primary" size="large" @click="saveForm" :loading="isSaving">保存设计方案</el-button>
        <el-button size="large" @click="previewMarkdown">预览Markdown</el-button>
        <!-- <el-button size="large" @click="resetForm">重置表单</el-button> -->
        <el-button type="success" size="large" @click="generateCode" :loading="isGeneratingCode" :disabled="!props.taskId">
          <el-icon><Tools /></el-icon>
          生成代码
        </el-button>
      </div>
    </el-form>

    <!-- Markdown预览对话框 -->
    <el-dialog v-model="showPreview" title="Markdown预览" width="80%" :before-close="closePreview">
      <el-scrollbar height="60vh">
        <div class="markdown-preview" v-html="markdownPreview"></div>
      </el-scrollbar>
      <template #footer>
        <el-button @click="closePreview">关闭</el-button>
        <el-button type="primary" @click="copyMarkdown">复制Markdown</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Tools, Loading } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { useWebSocketStore } from '../stores/websocket'

// Props
const props = defineProps({
  taskId: {
    type: String,
    default: ''
  },
  taskStatus: {
    type: String,
    default: ''
  },
  initialData: {
    type: Object,
    default: () => ({})
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['save', 'change'])

// WebSocket store for axios instance
const wsStore = useWebSocketStore()

// 检查store中的api是否是有效的axios实例
const isValidAxiosInstance = (instance) => {
  return instance && typeof instance.get === 'function'
}

// 如果store中没有提供有效的api实例，则直接创建axios实例
import axios from 'axios'
const apiInstance = isValidAxiosInstance(wsStore.api) ? wsStore.api : axios.create({
  baseURL: window.location.origin, // 使用当前域名，确保通过Vite代理
  timeout: 900000, // 15分钟超时
  headers: {
    'Content-Type': 'application/json',
  }
})

// 默认技术栈模板
const DEFAULT_TECHNOLOGY = `- 后端框架：Spring Boot 2.7.x + Spring Cloud 2021.x
- 数据访问：MyBatis Plus 3.5.x
- 数据库：MySQL 8.0
- 缓存：Redis 6.0
- 分布式锁：redisson
- 消息队列：Apache RocketMQ
- 服务发现：Nacos
- 配置中心：Nacos
- 后端分页：pageHelper
- 调度框架：XXL-JOB
- Excel处理：Alibaba EasyExcel
- 日志和监控：SLF4J
- 注解和工具：Lombok
- 部署：将代码提交到git分支即可
- 开发语言版本：java 1.8`

// 响应式数据
const isSaving = ref(false)
const isLoading = ref(false)
const isGeneratingCode = ref(false)
const showPreview = ref(false)
const markdownPreview = ref('')

// 表单数据结构
const formData = ref({
  project_name: '业务系统优化',
  version: 'V0.1',
  project_intro: {
    background: '',
    goal: ''
  },
  function_requirements: [],
  project_architecture: '采用微服务架构模式，实现松耦合、高可扩展的系统设计：',
  service_numbers: 2,
  services: [],
  data_resources: 2,
  databases: [],
  technology: DEFAULT_TECHNOLOGY,
  service_designs: [],
  execution: {
    service_scope: '本次没有新增服务，服务范围为：',
    services: [],
    data_scope: '本次没有新增数据库，数据库范围为：',
    databases: [],
    scope_interface: '本次新增接口，已经按服务范围进行划分，详见设计文档2服务设计部分。'
  }
})

// 创建markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

// 映射接口类型到前端下拉框选项
const mapInterfaceType = (backendType) => {
  const typeMap = {
    '新增': '新增', 
    '修改': '修改',
    '删除': '删除',
    'CREATE': '新增',
    'UPDATE': '修改', 
    'DELETE': '删除',
    'POST': '新增',
    'PUT': '修改',
    'PATCH': '修改'
  }
  return typeMap[backendType] || '新增'
}

// 转换分析结果数据到表单数据结构（适配新的API响应格式）
const convertAnalysisDataToFormData = (analysisData) => {
  console.log('🔄 开始转换分析结果数据:', analysisData)
  const convertedData = {}
  
  // 基本信息从文档解析结果获取
  const docParsing = analysisData.document_parsing?.data || {}
  const fileFormat = docParsing.fileFormat || {}
  const contentSummary = docParsing.documentStructure?.contentSummary || {}
  
  convertedData.project_name = fileFormat.fileName || '业务系统优化项目'
  convertedData.version = 'V0.1'
  
  // 项目介绍信息
  convertedData.project_intro = {
    background: contentSummary.abstract || '基于当前业务发展需要，现有系统在性能、用户体验等方面存在优化空间，需要进行系统性改进。',
    goal: '通过系统架构优化和功能升级，提升系统性能、改善用户体验，支撑业务快速发展。'
  }
  
  // 功能需求从变更分析获取
  convertedData.function_requirements = []
  const contentAnalysis = analysisData.content_analysis?.data || {}
  const changeAnalyses = contentAnalysis.change_analysis?.change_analyses || []
  
  if (changeAnalyses.length > 0) {
    changeAnalyses.forEach((change, index) => {
      convertedData.function_requirements.push({
        name: `${change.changeType}需求${index + 1}`,
        adjust_info: change.changeReason || change.changeDetails?.substring(0, 200) || '功能调整需求',
        filter_fields: [],
        list_fields: [],
        remarks: `变更类型: ${change.changeType}`
      })
    })
  } else {
    // 默认功能需求
    convertedData.function_requirements.push({
      name: '系统优化需求',
      adjust_info: '优化现有业务功能，提升系统性能和用户体验',
      filter_fields: [],
      list_fields: [],
      remarks: '基于现有业务场景进行针对性优化改进'
    })
  }
  
  // 项目架构信息
  convertedData.project_architecture = '采用微服务架构模式，实现松耦合、高可扩展的系统设计'
  
  // 服务数量和服务信息（从API名称推断）
  const apiNames = contentSummary.apiName || []
  const functionNames = contentSummary.functionName || []
  
  convertedData.service_numbers = Math.max(2, apiNames.length, Math.ceil(functionNames.length / 2))
  convertedData.services = []
  
  // 根据功能名称生成服务信息
  if (functionNames.length > 0) {
    functionNames.forEach((funcName, index) => {
      convertedData.services.push({
        service_name: funcName.includes('接口') ? '接口服务' : funcName.includes('额度') ? '额度管理服务' : '业务服务',
        service_english_name: `service-${index + 1}`
      })
    })
  } else {
    // 默认服务
    convertedData.services = [
      { service_name: '用户服务', service_english_name: 'user-service' },
      { service_name: '业务服务', service_english_name: 'business-service' }
    ]
  }
  
  // 数据库资源
  convertedData.data_resources = 2
  convertedData.databases = [
    { data_type: 'mysql', description: 'MySQL数据库' },
    { data_type: 'redis', description: 'Redis缓存' }
  ]
  
  // 技术栈
  convertedData.technology = DEFAULT_TECHNOLOGY
  
  // 服务详细设计 - 核心部分
  convertedData.service_designs = []
  
  // 从变更分析和API信息生成服务设计
  if (apiNames.length > 0) {
    apiNames.forEach((apiName, index) => {
      // 找到相关的变更分析
      const relatedChange = changeAnalyses.find(change => 
        change.changeDetails && change.changeDetails.includes(apiName)
      ) || changeAnalyses[index] || changeAnalyses[0]
      
      const apis = [{
        interface_type: relatedChange?.changeType === '新增' ? '新增' : relatedChange?.changeType === '修改' ? '修改' : '查询',
        uri: `/api/${apiName.replace(/[^a-zA-Z0-9]/g, '').toLowerCase()}`,
        method: relatedChange?.changeType === '新增' ? 'POST' : 'GET',
        description: apiName,
        request_params: '{\n  "param1": "value1",\n  "param2": "value2"\n}',
        response_params: '{\n  "success": true,\n  "data": {},\n  "message": "操作成功"\n}',
        special_requirements: relatedChange?.changeReason || '需要权限验证'
      }]
      
      convertedData.service_designs.push({
        service_name: convertedData.services[index]?.service_name || `服务${index + 1}`,
        service_english_name: convertedData.services[index]?.service_english_name || `service-${index + 1}`,
        service_duty: relatedChange?.changeReason || '核心业务逻辑处理',
        core_modules: relatedChange?.changeItems?.join('\n- ') || '- 核心业务模块\n- 数据处理模块',
        apis: apis,
        data_table_sql: `-- ${apiName}相关数据表\nCREATE TABLE t_${apiName.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()} (\n  id BIGINT PRIMARY KEY AUTO_INCREMENT,\n  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);`,
        dependence_service: '无'
      })
    })
  } else {
    // 如果没有API信息，基于变更分析生成默认服务设计
    const maxServices = Math.min(convertedData.services.length, 2)
    for (let i = 0; i < maxServices; i++) {
      const relatedChange = changeAnalyses[i] || changeAnalyses[0]
      
      convertedData.service_designs.push({
        service_name: convertedData.services[i]?.service_name || `服务${i + 1}`,
        service_english_name: convertedData.services[i]?.service_english_name || `service-${i + 1}`,
        service_duty: relatedChange?.changeReason || '核心业务逻辑处理',
        core_modules: relatedChange?.changeItems?.slice(0, 3).join('\n- ') || '- 核心业务模块\n- 数据处理模块',
        apis: [{
          interface_type: relatedChange?.changeType === '新增' ? '新增' : '查询',
          uri: `/api/${convertedData.services[i]?.service_english_name || `service${i + 1}`}/list`,
          method: relatedChange?.changeType === '新增' ? 'POST' : 'GET',
          description: relatedChange?.changeItems?.[0] || `${convertedData.services[i]?.service_name || '服务'}接口`,
          request_params: '{\n  "param1": "value1"\n}',
          response_params: '{\n  "success": true,\n  "data": []\n}',
          special_requirements: '需要登录权限验证'
        }],
        data_table_sql: `-- ${convertedData.services[i]?.service_name || '服务'}数据表\nCREATE TABLE t_${convertedData.services[i]?.service_english_name?.replace(/-/g, '_') || `service_${i + 1}`} (\n  id BIGINT PRIMARY KEY AUTO_INCREMENT,\n  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);`,
        dependence_service: '无'
      })
    }
  }
  
  // 执行要求
  convertedData.execution = {
    service_scope: '本次没有新增服务，服务范围为：',
    services: convertedData.services.map(service => ({
      service_name: service.service_name,
      service_english_name: service.service_english_name,
      gitlab: ''
    })),
    data_scope: '本次没有新增数据库，数据库范围为：',
    databases: [],
    scope_interface: '本次新增接口，已经按服务范围进行划分，详见设计文档2服务设计部分。'
  }
  
  console.log('🎯 分析结果转换完成:', convertedData)
  console.log('🔌 生成的服务设计数量:', convertedData.service_designs.length)
  console.log('🔌 总API数量:', convertedData.service_designs.reduce((total, service) => total + service.apis.length, 0))
  
  return convertedData
}

// 转换后端数据结构到前端表单结构
const convertBackendDataToFormData = (backendData) => {
  console.log('🔄 开始转换后端数据:', backendData)
  const convertedData = {}
  
  // 检查数据结构类型
  const isAnalysisResult = backendData.ai_analysis || backendData.content_analysis || backendData.document_parsing
  
  if (isAnalysisResult) {
    console.log('🔍 检测到分析结果数据格式，进行适配转换')
    return convertAnalysisDataToFormData(backendData)
  }
  
  // 原有的表单数据转换逻辑
  console.log('📋 使用原有表单数据转换逻辑')
  
  // 基本信息
  convertedData.project_name = backendData.project_name || '业务系统优化项目'
  convertedData.version = 'V0.1'
  
  // 项目介绍信息转换 - 修复字段映射
  const projectInfo = backendData.project_info || ''
  convertedData.project_intro = {
    background: backendData.project_background || projectInfo || '基于当前业务发展需要，现有系统在性能、用户体验等方面存在优化空间，需要进行系统性改进。',
    goal: backendData.project_goal || projectInfo || '通过系统架构优化和功能升级，提升系统性能、改善用户体验，支撑业务快速发展。'
  }
  
  console.log('📋 项目介绍转换结果:', convertedData.project_intro)
  
  // 功能需求信息转换 - 修复字段映射
  convertedData.function_requirements = []
  if (backendData.function_requirements_info) {
    const reqInfo = backendData.function_requirements_info
    convertedData.function_requirements.push({
      name: '功能调整需求',
      adjust_info: reqInfo.adjust_info || reqInfo || '根据业务需求进行系统功能调整和优化',
      filter_fields: [],
      list_fields: [],
      remarks: reqInfo.remarks || '按照业务需求进行功能调整和优化'
    })
    console.log('📋 功能需求转换结果:', convertedData.function_requirements)
  } else {
    // 默认功能需求
    convertedData.function_requirements.push({
      name: '系统优化需求',
      adjust_info: '优化现有业务功能，提升系统性能和用户体验',
      filter_fields: [],
      list_fields: [],
      remarks: '基于现有业务场景进行针对性优化改进'
    })
  }
  
  // 项目架构信息转换
  convertedData.project_architecture = backendData.project_architecture || '采用微服务架构模式，实现松耦合、高可扩展的系统设计'
  
  // 服务数量和服务信息
  convertedData.service_numbers = backendData.service_numbers || 2
  convertedData.services = []
  
  // 从service_info转换服务基本信息
  if (backendData.service_info && Array.isArray(backendData.service_info)) {
    convertedData.services = backendData.service_info.map(service => ({
      service_name: service.service_name || '',
      service_english_name: service.service_english_name || ''
    }))
  } else if (backendData.service_details && Array.isArray(backendData.service_details)) {
    // 如果service_info不存在，从service_details提取
    convertedData.services = backendData.service_details.map(service => ({
      service_name: service.service_name || '',
      service_english_name: service.service_english_name || ''
    }))
  }
  
  // 数据库资源
  convertedData.data_resources = backendData.data_resources || 2
  convertedData.databases = []
  if (backendData.data_info && Array.isArray(backendData.data_info)) {
    convertedData.databases = backendData.data_info.map((db, index) => ({
      data_type: db.data_type || 'mysql',
      description: db.data_type === 'mysql' ? 'MySQL数据库' : (db.data_type === 'redis' ? 'Redis缓存' : db.data_type)
    }))
  }
  
  // 技术栈转换
  if (backendData.technology) {
    const tech = backendData.technology
    convertedData.technology = `- 后端框架：${tech.后端框架 || 'Spring Boot 2.7.x + Spring Cloud 2021.x'}
- 数据访问：${tech.数据访问 || 'MyBatis Plus 3.5.x'}
- 数据库：${tech.数据库 || 'MySQL 8.0'}
- 缓存：${tech.缓存 || 'Redis 6.0'}
- 分布式锁：${tech.分布式锁 || 'redisson'}
- 消息队列：${tech.消息队列 || 'Apache RocketMQ'}
- 服务发现：${tech.服务发现 || 'Nacos'}
- 配置中心：${tech.配置中心 || 'Nacos'}
- 后端分页：${tech.后端分页 || 'pageHelper'}
- 调度框架：${tech.调度框架 || 'XXL-JOB'}
- Excel处理：${tech.Excel处理 || 'Alibaba EasyExcel'}
- 日志和监控：${tech.日志和监控 || 'SLF4J'}
- 注解和工具：${tech.注解和工具 || 'Lombok'}
- 部署：${tech.部署 || '将代码提交到git分支即可'}
- 开发语言版本：${tech.开发语言版本 || 'java 1.8'}`
  } else {
    convertedData.technology = DEFAULT_TECHNOLOGY
  }
  
  // 服务详细设计转换 - 修复API设计映射
  console.log('🔄 开始转换服务详细设计，原始数据:', backendData.service_details)
  convertedData.service_designs = []
  if (backendData.service_details && Array.isArray(backendData.service_details)) {
    convertedData.service_designs = backendData.service_details.map((service, index) => {
      console.log(`🔄 转换第${index + 1}个服务:`, service.service_name, service)
      
      // 处理API设计数据 - 将后端的API设计转换为前端期望的apis数组
      let apis = []
      if (service.api_design && Array.isArray(service.api_design)) {
        console.log(`✅ 发现API设计数组，长度: ${service.api_design.length}`)
        apis = service.api_design.map((apiItem, apiIndex) => {
          console.log(`  - API ${apiIndex + 1}:`, apiItem)
          return {
            interface_type: mapInterfaceType(apiItem.interface_type),
            uri: apiItem.uri || '',
            method: apiItem.method || 'GET',
            description: apiItem.description || '',
            request_params: typeof apiItem.request_params === 'object' ? 
              JSON.stringify(apiItem.request_params, null, 2) : (apiItem.request_params || '{}'),
            response_params: typeof apiItem.response_params === 'object' ? 
              JSON.stringify(apiItem.response_params, null, 2) : (apiItem.response_params || '{}'),
            special_requirements: apiItem.special_requirements || ''
          }
        })
      } else if (service.api_design && typeof service.api_design === 'object') {
        console.log('⚠️ API设计是对象而不是数组:', service.api_design)
        // 如果API设计是单个对象
        const apiItem = service.api_design
        apis = [{
          interface_type: mapInterfaceType(apiItem.interface_type),
          uri: apiItem.uri || '',
          method: apiItem.method || 'GET', 
          description: apiItem.description || '',
          request_params: typeof apiItem.request_params === 'object' ? 
            JSON.stringify(apiItem.request_params, null, 2) : (apiItem.request_params || '{}'),
          response_params: typeof apiItem.response_params === 'object' ? 
            JSON.stringify(apiItem.response_params, null, 2) : (apiItem.response_params || '{}'),
          special_requirements: apiItem.special_requirements || ''
        }]
      }
      
      // 如果没有API设计，添加默认的API
      if (apis.length === 0) {
        console.log('⚠️ 没有找到API设计，创建默认API')
        apis = [{
          interface_type: '新增',
          uri: `/api/${(service.service_english_name || 'service').replace('-', '/')}/create`,
          method: 'POST',
          description: `${service.service_name || '服务'}数据新增接口`,
          request_params: '{\n  "page": 1,\n  "size": 10\n}',
          response_params: '{\n  "success": true,\n  "data": [],\n  "total": 0\n}',
          special_requirements: '需要登录权限验证'
        }]
      }
      
      console.log(`🔄 服务 ${service.service_name} API转换结果(${apis.length}个):`, apis)
      
      const convertedService = {
        service_name: service.service_name || '',
        service_english_name: service.service_english_name || '',
        service_duty: service.service_duty || '',
        core_modules: service.core_modules || '',
        apis: apis, // 添加转换后的APIs数组
        data_table_sql: service.api_design && service.api_design[0] ? service.api_design[0].data_table_sql || '' : '',
        dependence_service: service.api_design && service.api_design[0] && service.api_design[0].dependence_service ? 
          (Array.isArray(service.api_design[0].dependence_service) ? service.api_design[0].dependence_service.join(', ') : service.api_design[0].dependence_service) : ''
      }
      
      console.log(`✅ 第${index + 1}个服务转换完成:`, convertedService)
      return convertedService
    })
  }
  
  console.log('🎯 服务设计转换完成，共', convertedData.service_designs.length, '个服务:', convertedData.service_designs)
  
  // 执行要求转换 - 修复数据结构映射
  convertedData.execution = {
    service_scope: '本次没有新增服务，服务范围为：',
    services: convertedData.services || [],
    data_scope: '本次没有新增数据库，数据库范围为：',
    databases: [],
    scope_interface: '本次新增接口，已经按服务范围进行划分，详见设计文档2服务设计部分。'
  }
  
  if (backendData.execution) {
    const exec = backendData.execution
    convertedData.execution.service_scope = exec.service_scope || convertedData.execution.service_scope
    convertedData.execution.data_scope = exec.data_scope || convertedData.execution.data_scope
    convertedData.execution.scope_interface = exec.scope_interface || convertedData.execution.scope_interface
    
    // 处理服务
    if (exec.services && Array.isArray(exec.services)) {
      convertedData.execution.services = exec.services
    }
    
    // 处理数据库
    if (exec.databases && Array.isArray(exec.databases)) {
      convertedData.execution.databases = exec.databases
    }
  }
  
  // 确保execution.services有正确的结构
  if (convertedData.services && Array.isArray(convertedData.services)) {
    convertedData.execution.services = convertedData.services.map(service => ({
      service_name: service.service_name || '',
      service_english_name: service.service_english_name || '',
      gitlab: '' // 添加gitlab字段
    }))
  }
  
  console.log('🎯 最终转换结果:', convertedData)
  return convertedData
}

// 优化的响应式数据更新方法
const updateFormDataReactively = (newData) => {
  console.log('📥 准备更新表单数据:', newData)
  
  // 特别处理service_designs数组 - 直接替换确保响应式更新
  if (newData.service_designs && Array.isArray(newData.service_designs)) {
    console.log('🔧 直接更新service_designs数组，包含APIs:', newData.service_designs.map(s => ({
      name: s.service_name,
      apisCount: s.apis ? s.apis.length : 0,
      apis: s.apis
    })))
    
    // 深度克隆数据以确保响应式更新
    const clonedServiceDesigns = JSON.parse(JSON.stringify(newData.service_designs))
    formData.value.service_designs = clonedServiceDesigns
    
    // 添加额外的调试信息
    console.log('🔍 service_designs更新后验证:')
    formData.value.service_designs.forEach((service, index) => {
      console.log(`  服务${index + 1}: ${service.service_name}`)
      if (service.apis && service.apis.length > 0) {
        service.apis.forEach((api, apiIndex) => {
          console.log(`    API${apiIndex + 1}: interface_type="${api.interface_type}", method="${api.method}"`)
        })
      }
    })
  }
  
  // 对其他字段使用递归更新
  for (const key in newData) {
    if (key === 'service_designs') continue // 已经单独处理过了
    
    if (newData.hasOwnProperty(key)) {
      if (typeof newData[key] === 'object' && newData[key] !== null && !Array.isArray(newData[key])) {
        // 对于对象类型，递归更新
        if (!formData.value[key]) formData.value[key] = {}
        Object.assign(formData.value[key], newData[key])
      } else {
        // 对于基本类型和数组，直接赋值
        formData.value[key] = newData[key]
      }
    }
  }
  
  // 添加新的属性（如果存在）
  for (const key in newData) {
    if (!formData.value.hasOwnProperty(key) && key !== 'service_designs') {
      formData.value[key] = newData[key]
    }
  }
  
  console.log('✅ 表单数据更新完成，当前service_designs:', formData.value.service_designs)
  console.log('🔍 formData.value.service_designs长度:', formData.value.service_designs?.length)
  console.log('🔍 检查第一个服务:', formData.value.service_designs?.[0])
}

// 加载表单数据从API
const loadFormData = async () => {
  console.log('🔥🔥🔥 === loadFormData 开始 === 🔥🔥🔥')
  console.log('🔥 props.taskId:', props.taskId)
  
  if (!props.taskId) {
    console.log('❌ 没有提供任务ID，使用默认数据')
    return
  }
  
  try {
    isLoading.value = true
    const requestUrl = `/api/file/design-form/${props.taskId}`
    console.log('🚀🚀🚀 准备发送GET请求到:', requestUrl)
    
    // 使用配置好的axios实例
    const response = await apiInstance.get(requestUrl)
    
    console.log('✅✅✅ API响应成功，状态码:', response.status)
    console.log('📄📄📄 API响应原始数据:', response.data)
    
    if (response.data.success) {
      let loadedData
      
      // 检查是否有form_data字段（旧格式）
      if (response.data.form_data) {
        loadedData = response.data.form_data
        console.log('✅✅✅ 成功获取表单数据（旧格式）:', loadedData)
      } else {
        // 使用分析结果数据（新格式）
        loadedData = response.data
        console.log('✅✅✅ 成功获取分析结果数据（新格式）:', loadedData)
      }
      
      // 转换后端数据结构到前端表单结构
      const convertedData = convertBackendDataToFormData(loadedData)
      console.log('🔄🔄🔄 转换后的表单数据:', convertedData)
      
        // 使用优化的响应式更新方法
  updateFormDataReactively(convertedData)
  
  // 强制触发Vue响应式更新
  nextTick(() => {
    console.log('⚡ 强制触发响应式更新')
    // 触发Vue的深度响应式检查
    formData.value = { ...formData.value }
  })
  
  console.log('✅✅✅ 表单数据已更新到formData.value:', formData.value)
      ElMessage.success('表单数据加载成功')
    } else {
      console.log('⚠️⚠️⚠️ API返回失败')
      console.log('response.data:', response.data)
      ElMessage.error('API返回失败: ' + (response.data.error || '未知错误'))
    }
  } catch (error) {
    console.error('❌❌❌ 加载表单数据失败:', error)
    ElMessage.error('加载表单数据失败: ' + error.message)
  } finally {
    isLoading.value = false
    console.log('🔥🔥🔥 === loadFormData 完成 === 🔥🔥🔥')
  }
}

// 初始化表单数据
const initializeFormData = () => {
  console.log('=== initializeFormData 开始 ===')
  console.log('检查初始数据 props.initialData:', props.initialData)

  // 此函数不再负责加载API数据，仅处理无taskId时的默认状态
  // 如果有初始数据，则使用初始数据
  if (props.initialData && Object.keys(props.initialData).length > 0) {
    console.log('使用 props.initialData 初始化表单')
    Object.assign(formData.value, props.initialData)
  } else {
    console.log('使用默认数据初始化表单，并添加默认项目')
    // 添加默认的功能需求
    addRequirement()
    // 添加默认的服务
    addService()
    addService()
    // 添加默认的数据库
    addDatabase()
    addDatabase()
    // 添加默认的服务设计
    addServiceDesign()
    // 添加默认的执行服务
    addExecutionService()
    addExecutionService()
    // 添加默认的执行数据库
    addExecutionDatabase()
    addExecutionDatabase()
  }
  
  console.log('=== initializeFormData 完成 ===')
}

// 功能需求相关方法
const addRequirement = () => {
  formData.value.function_requirements.push({
    name: '功能调整',
    adjust_info: '',
    filter_fields: [],
    list_fields: [],
    remarks: ''
  })
}

const removeRequirement = (index) => {
  formData.value.function_requirements.splice(index, 1)
}

const addField = (requirement, fieldType) => {
  const newField = {
    name: '',
    type: '',
    length: '',
    default_value: '',
    required: '否',
    rules: ''
  }
  
  if (!requirement[fieldType]) {
    requirement[fieldType] = []
  }
  requirement[fieldType].push(newField)
}

const removeField = (fields, index) => {
  fields.splice(index, 1)
}

// 服务相关方法
const addService = () => {
  formData.value.services.push({
    service_name: '',
    service_english_name: ''
  })
}

const removeService = (index) => {
  formData.value.services.splice(index, 1)
  formData.value.service_numbers = formData.value.services.length
}

// 数据库相关方法
const addDatabase = () => {
  formData.value.databases.push({
    data_type: 'mysql',
    description: ''
  })
}

const removeDatabase = (index) => {
  formData.value.databases.splice(index, 1)
  formData.value.data_resources = formData.value.databases.length
}

// 服务设计相关方法
const addServiceDesign = () => {
  formData.value.service_designs.push({
    service_name: '',
    service_english_name: '',
    service_duty: '',
    core_modules: '',
    apis: [{
      interface_type: '新增',
      uri: '',
      method: 'GET',
      description: '',
      request_params: '{}',
      response_params: '{}',
      special_requirements: ''
    }], // 确保默认有一个API
    data_table_sql: '',
    dependence_service: ''
  })
}

const removeServiceDesign = (index) => {
  formData.value.service_designs.splice(index, 1)
}

const addApi = (service) => {
  if (!service.apis) {
    service.apis = []
  }
  service.apis.push({
    interface_type: '新增',
    uri: '',
    method: 'GET',
    description: '',
    request_params: '{}',
    response_params: '{}',
    special_requirements: ''
  })
}

const removeApi = (apis, index) => {
  apis.splice(index, 1)
}

// 执行要求相关方法
const addExecutionService = () => {
  formData.value.execution.services.push({
    service_name: '',
    service_english_name: '',
    gitlab: ''
  })
}

const removeExecutionService = (index) => {
  formData.value.execution.services.splice(index, 1)
}

const addExecutionDatabase = () => {
  formData.value.execution.databases.push({
    data_type: 'mysql',
    config: ''
  })
}

const removeExecutionDatabase = (index) => {
  formData.value.execution.databases.splice(index, 1)
}

// Markdown生成器 - 拆分为多个小函数提高可维护性

// 生成文档头部
const generateMarkdownHeader = () => {
  return `设计文档 - ${formData.value.project_name}${formData.value.version}\n\n`
}

// 生成项目介绍部分
const generateProjectIntroSection = () => {
  let markdown = '1. 系统架构设计\n\n'
  
  // 1.1 项目介绍
  markdown += '1.1 项目介绍\n\n'
  markdown += `${formData.value.project_intro.background}\n`
  
  
  return markdown
}

// 生成功能需求说明部分
const generateFunctionRequirementsSection = () => {
  let markdown = '1.2 功能需求说明\n\n'
  formData.value.function_requirements.forEach((req, index) => {
    markdown += `1.2.${index + 1} ${req.name}\n`
    markdown += `调整说明:${req.adjust_info}\n`
    if (req.remarks) {
      markdown += `备注：${req.remarks}\n`
    }
    markdown += '\n'
  })
  
  return markdown
}

// 生成总体架构部分
const generateArchitectureSection = () => {
  let markdown = '1.3 总体架构\n'
  markdown += `${formData.value.project_architecture}\n`
  markdown += `- 涉及${formData.value.service_numbers}个后端服务：\n`
  formData.value.services.forEach((service, index) => {
    markdown += `${index + 1}. ${service.service_name}：${service.service_english_name}\n`
  })
  markdown += '\n- 涉及数据库：\n'
  formData.value.databases.forEach((db, index) => {
    markdown += `${index + 1}. ${db.description}：${db.data_type.toUpperCase()}\n`
  })
  markdown += '\n'
  
  return markdown
}

// 生成技术栈选型部分
const generateTechnologyStackSection = () => {
  return `1.4 技术栈选型\n${formData.value.technology}\n\n`
}

// 生成服务设计部分
const generateServiceDesignSection = () => {
  let markdown = '2. 服务设计\n\n'
  
  formData.value.service_designs.forEach((service, serviceIndex) => {
    markdown += `2.${serviceIndex + 1} ${service.service_name} (${service.service_english_name})\n`
    markdown += `职责：${service.service_duty}\n\n`
    
    markdown += `2.${serviceIndex + 1}.1 核心模块：\n`
    markdown += `${service.core_modules}\n\n`
    
    markdown += `2.${serviceIndex + 1}.2 API设计：\n`
    if (service.apis && service.apis.length > 0) {
      service.apis.forEach((api, apiIndex) => {
        markdown += `2.${serviceIndex + 1}.2.${apiIndex + 1} ${api.interface_type}接口：\n`
        markdown += `uri : ${api.uri}\n`
        markdown += `method: ${api.method}\n`
        markdown += `description:${api.description}\n`
        markdown += `入参示例：\n${api.request_params}\n\n`
        markdown += `返参示例：\n${api.response_params}\n\n`
        if (api.special_requirements) {
          markdown += `特殊要求：\n${api.special_requirements}\n\n`
        }
      })
    }
    
    if (service.data_table_sql) {
      markdown += `2.${serviceIndex + 1}.3 数据库表设计：\n`
      markdown += `${service.data_table_sql}\n\n`
    }
    
    markdown += `2.${serviceIndex + 1}.4 本次项目依赖服务：\n`
    markdown += `依赖服务名称：${service.dependence_service || '无'}\n\n`
  })
  
  return markdown
}

// 生成执行要求部分
const generateExecutionRequirementsSection = () => {
  let markdown = '3 执行要求\n\n'
  
  // 3.1 涉及服务范围
  markdown += '3.1 涉及服务范围\n'
  markdown += `${formData.value.execution.service_scope}\n`
  formData.value.execution.services.forEach((service, index) => {
    markdown += `${index + 1}. ${service.service_name}：${service.service_english_name}，git地址：${service.gitlab}\n`
  })
  markdown += '\n'
  
  // 3.2 涉及数据库范围
  markdown += '3.2 涉及数据库范围\n'
  markdown += `${formData.value.execution.data_scope}\n`
  if (formData.value.execution.databases && formData.value.execution.databases.length > 0) {
    formData.value.execution.databases.forEach((db, index) => {
      markdown += `3.2.${index + 1} ${db.data_type}:\n`
      markdown += `${db.config}\n\n`
    })
  }
  
  // 3.3 涉及接口范围
  markdown += '3.3 涉及接口范围\n'
  markdown += `${formData.value.execution.scope_interface}\n`
  
  return markdown
}

// 主要的Markdown生成函数 - 现在变得简洁易维护
const generateMarkdown = () => {
  let markdown = ''
  
  try {
    markdown += generateMarkdownHeader()
    markdown += generateProjectIntroSection()
    markdown += generateFunctionRequirementsSection()
    markdown += generateArchitectureSection()
    markdown += generateTechnologyStackSection()
    markdown += generateServiceDesignSection()
    markdown += generateExecutionRequirementsSection()
    
    console.log('生成的Markdown内容长度:', markdown.length)
    return markdown
  } catch (error) {
    console.error('生成Markdown时出错:', error)
    ElMessage.error('生成设计方案时出错: ' + error.message)
    return ''
  }
}

// 表单操作方法
const saveForm = async () => {
  try {
    isSaving.value = true
    
    // 生成markdown内容
    const markdownContent = generateMarkdown()
    
    // 构建保存数据
    const saveData = {
      form_data: formData.value,
      markdown_content: markdownContent
    }
    
    // 触发保存事件
    emit('save', saveData)
    
    ElMessage.success('设计方案保存成功')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    isSaving.value = false
  }
}

const previewMarkdown = () => {
  const markdown = generateMarkdown()
  markdownPreview.value = md.render(markdown)
  showPreview.value = true
}

const closePreview = () => {
  showPreview.value = false
}

const copyMarkdown = async () => {
  try {
    const markdown = generateMarkdown()
    await navigator.clipboard.writeText(markdown)
    ElMessage.success('Markdown内容已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const resetForm = () => {
  // 重置为初始状态
  Object.assign(formData.value, {
    project_name: '业务系统优化',
    version: 'V0.1',
    project_intro: { background: '', goal: '' },
    function_requirements: [],
    project_architecture: '采用微服务架构模式，实现松耦合、高可扩展的系统设计：',
    service_numbers: 2,
    services: [],
    data_resources: 2,
    databases: [],
    technology: DEFAULT_TECHNOLOGY,
    service_designs: [],
    execution: {
      service_scope: '本次没有新增服务，服务范围为：',
      services: [],
      data_scope: '本次没有新增数据库，数据库范围为：',
      databases: [],
      scope_interface: '本次新增接口，已经按服务范围进行划分，详见设计文档2服务设计部分。'
    }
  })
  
  // 确保execution.services有正确的初始结构
  if (formData.value.services && Array.isArray(formData.value.services)) {
    formData.value.execution.services = formData.value.services.map(service => ({
      service_name: service.service_name || '',
      service_english_name: service.service_english_name || '',
      gitlab: ''
    }))
  }
  
  initializeFormData()
  ElMessage.success('表单已重置')
}

// 验证Markdown内容的质量
const validateMarkdownContent = (content) => {
  const errors = []
  const warnings = []
  
  // 基本检查
  if (!content || content.trim().length < 100) {
    errors.push('设计方案内容过短，请完善后再生成代码')
    return { isValid: false, errors, warnings }
  }
  
  // 检查必要的章节
  const requiredSections = [
    '系统架构设计',
    '服务设计', 
    '执行要求'
  ]
  
  requiredSections.forEach(section => {
    if (!content.includes(section)) {
      warnings.push(`缺少"${section}"章节，建议完善`)
    }
  })
  
  // 检查是否包含技术栈信息
  if (!content.includes('技术栈') && !content.includes('Spring Boot')) {
    warnings.push('建议添加技术栈选型信息')
  }
  
  // 检查是否包含API设计
  if (!content.includes('API设计') && !content.includes('接口')) {
    warnings.push('建议添加API接口设计信息')
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings
  }
}

// 生成代码方法
const generateCode = async () => {
  if (!props.taskId) {
    ElMessage.warning('无法获取任务ID，请重新分析文档')
    return
  }
  
  // 生成markdown内容
  const markdownContent = generateMarkdown()
  if (!markdownContent) {
    ElMessage.warning('没有设计方案内容可生成代码')
    return
  }
  
  // 验证Markdown内容
  const validation = validateMarkdownContent(markdownContent)
  if (!validation.isValid) {
    ElMessage.error(validation.errors.join('; '))
    return
  }
  
  // 显示警告信息（如果有）
  if (validation.warnings.length > 0) {
    ElMessage.warning(validation.warnings.join('; '))
  }
  
  isGeneratingCode.value = true
  
  try {
    // 获取项目名称，优先从表单数据中获取
    const projectName = formData.value.project_name || '业务系统优化'
    
    // 使用fetch API发送请求
    const response = await fetch('/api/coder-agent/process-document', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_content: markdownContent,
        project_name: projectName,
        project_task_id: props.taskId
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    
    if (response.data.status === 'success') {
      ElMessage.success('代码生成成功！请查看后端输出目录')
      
      // 可以在这里添加更多成功后的处理逻辑
      if (response.data.data) {
        console.log('生成结果:', response.data.data)
      }
    } else {
      ElMessage.error('代码生成失败: ' + (response.data.message || '未知错误'))
    }
  } catch (error) {
    console.error('代码生成失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error('代码生成失败: ' + errorMsg)
  } finally {
    isGeneratingCode.value = false
  }
}

// 监听表单数据变化
watch(formData, () => {
  emit('change', formData.value)
}, { deep: true })

// 监听services数量变化
watch(() => formData.value.services.length, (newLength) => {
  formData.value.service_numbers = newLength
})

// 监听databases数量变化
watch(() => formData.value.databases.length, (newLength) => {
  formData.value.data_resources = newLength
})

// 初始化
onMounted(() => {
  console.log('🚀 === DesignPlanForm mounted ===')
  // onMounted时，如果taskId还未传来，则初始化一个空的表单
  if (!props.taskId) {
    initializeFormData()
  }
  // 如果taskId已经存在，watch会负责加载数据
})

// 监听 taskId 变化，这是加载数据的唯一入口点
// 监听 taskId 变化，但不立即加载表单数据
watch(() => props.taskId, (newTaskId, oldTaskId) => {
  console.log('=== ♻️ taskId 监听器触发 ===')
  console.log(`taskId 从 ${oldTaskId} 变为 ${newTaskId}`)
  
  if (newTaskId) {
    console.log(`✅ 检测到有效 taskId: ${newTaskId}，但等待任务完成后再加载表单数据`)
    // 不立即调用 loadFormData()，等待任务完成
  } else {
    console.log('⚠️ taskId 变为无效值，重置表单')
    resetForm()
  }
}, { immediate: true })

// 新增：监听父组件传递的任务状态，只有当任务完成时才加载表单数据
watch(() => props.taskStatus, (newStatus, oldStatus) => {
  console.log('=== 📊 taskStatus 监听器触发 ===')
  console.log(`任务状态从 ${oldStatus} 变为 ${newStatus}`)
  
  if ((newStatus === 'completed' || newStatus === 'fully_completed') && props.taskId) {
    console.log(`✅ 任务已完成，开始加载表单数据: ${props.taskId}`)
    loadFormData()
  }
}, { immediate: false })
</script>

<style lang="scss" scoped>
.design-plan-form {
  padding: 20px;
  background: white;
  border-radius: 8px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  
  p {
    margin-top: 16px;
    color: #606266;
    font-size: 14px;
  }
}

.design-form {
  .form-section {
    margin-bottom: 40px;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 20px;
    
    h3 {
      margin: 0 0 20px 0;
      color: #303133;
      font-size: 18px;
      font-weight: 600;
      border-bottom: 2px solid #409eff;
      padding-bottom: 8px;
    }
  }
  
  .subsection {
    margin-bottom: 30px;
    
    h4 {
      margin: 0 0 16px 0;
      color: #606266;
      font-size: 16px;
      font-weight: 600;
      border-left: 4px solid #409eff;
      padding-left: 12px;
    }
  }
  
  .requirement-item {
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 16px;
    background: #fafafa;
    
    .requirement-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      h5 {
        margin: 0;
        color: #303133;
        font-size: 14px;
        font-weight: 600;
      }
    }
  }
  
  .field-item {
    margin-bottom: 8px;
    padding: 8px;
    background: white;
    border-radius: 4px;
  }
  
  .service-item,
  .database-item,
  .execution-service-item,
  .execution-db-item {
    margin-bottom: 12px;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 4px;
    
    h5 {
      margin: 0 0 8px 0;
      color: #303133;
      font-size: 14px;
      font-weight: 600;
    }
  }
  
  .service-design-item {
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    padding: 20px;
    margin-bottom: 20px;
    background: #fafafa;
    
    .service-design-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      
      h4 {
        margin: 0;
        color: #303133;
        font-size: 16px;
        font-weight: 600;
      }
    }
    
    .api-design {
      margin-bottom: 20px;
      
      h5 {
        margin: 0 0 16px 0;
        color: #606266;
        font-size: 14px;
        font-weight: 600;
        border-left: 3px solid #67c23a;
        padding-left: 8px;
      }
      
      .api-item {
        border: 1px solid #e4e7ed;
        border-radius: 4px;
        padding: 16px;
        margin-bottom: 12px;
        background: white;
        
        .api-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          
          h6 {
            margin: 0;
            color: #303133;
            font-size: 13px;
            font-weight: 600;
          }
        }
      }
    }
  }
}

.form-actions {
  margin-top: 40px;
  padding: 20px;
  text-align: center;
  border-top: 1px solid #e4e7ed;
  
  .el-button {
    margin: 0 8px;
  }
}

.markdown-preview {
  padding: 20px;
  background: #fafafa;
  border-radius: 6px;
  
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    color: #303133;
    margin: 16px 0 8px 0;
    font-weight: 600;
  }
  
  :deep(p) {
    margin: 8px 0;
    line-height: 1.6;
    color: #606266;
  }
  
  :deep(pre) {
    background: #2d3748;
    color: #e2e8f0;
    padding: 16px;
    border-radius: 6px;
    overflow-x: auto;
  }
  
  :deep(code) {
    background: #f1f2f3;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    color: #e6a23c;
  }
}
</style>