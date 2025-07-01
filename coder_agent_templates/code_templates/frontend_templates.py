#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端Vue2代码模版
提供Vue2项目的各种代码模版
"""

# Vue2 项目配置模版
VUE_PROJECT_CONFIG = """
{
  "name": "{{project_name}}",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "serve": "vue-cli-service serve",
    "build": "vue-cli-service build",
    "lint": "vue-cli-service lint",
    "test:unit": "vue-cli-service test:unit"
  },
  "dependencies": {
    "vue": "^2.6.14",
    "vue-router": "^3.5.4",
    "vuex": "^3.6.2",
    "axios": "^0.27.2",
    "element-ui": "^2.15.9",
    "moment": "^2.29.4"
  },
  "devDependencies": {
    "@vue/cli-plugin-eslint": "~5.0.0",
    "@vue/cli-plugin-router": "~5.0.0",
    "@vue/cli-plugin-unit-jest": "~5.0.0",
    "@vue/cli-plugin-vuex": "~5.0.0",
    "@vue/cli-service": "~5.0.0",
    "@vue/test-utils": "^1.3.0",
    "eslint": "^7.32.0",
    "eslint-plugin-vue": "^8.0.3",
    "vue-template-compiler": "^2.6.14"
  }
}
"""

# Vue配置文件模版
VUE_CONFIG_JS = """
const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:8081',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'
        }
      }
    }
  },
  chainWebpack: config => {
    config.plugin('html').tap(args => {
      args[0].title = '{{project_title}}'
      return args
    })
  }
})
"""

# 主App组件模版
VUE_APP_COMPONENT = """
<template>
  <div id="app">
    <div class="header">
      <h1>{{project_title}}</h1>
      <nav>
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/{{module_name}}" class="nav-link">{{module_title}}</router-link>
      </nav>
    </div>
    <main class="main-content">
      <router-view/>
    </main>
    <footer class="footer">
      <p>&copy; 2023 {{project_title}}. All rights reserved.</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background-color: #409EFF;
  color: white;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header h1 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
}

.header nav {
  display: flex;
  gap: 1rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-link:hover {
  background-color: rgba(255,255,255,0.1);
}

.nav-link.router-link-active {
  background-color: rgba(255,255,255,0.2);
}

.main-content {
  flex: 1;
  padding: 2rem;
  background-color: #f5f5f5;
}

.footer {
  background-color: #909399;
  color: white;
  text-align: center;
  padding: 1rem;
}
</style>
"""

# 主页面组件模版
VUE_HOME_COMPONENT = """
<template>
  <div class="home">
    <el-card class="welcome-card">
      <div slot="header" class="clearfix">
        <span class="card-title">欢迎使用 {{project_title}}</span>
      </div>
      <div class="welcome-content">
        <p>这是一个基于Vue2的现代化Web应用程序。</p>
        <el-button type="primary" @click="navigateToModule">
          开始使用 {{module_title}}
        </el-button>
      </div>
    </el-card>

    <!-- 功能特性展示 -->
    <el-row :gutter="20" class="features">
      <el-col :span="8" v-for="feature in features" :key="feature.id">
        <el-card shadow="hover" class="feature-card">
          <div class="feature-icon">
            <i :class="feature.icon"></i>
          </div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  name: 'Home',
  data() {
    return {
      features: [
        {
          id: 1,
          title: '现代化界面',
          description: '基于Element UI的美观界面设计',
          icon: 'el-icon-monitor'
        },
        {
          id: 2,
          title: '响应式设计',
          description: '适配各种设备和屏幕尺寸',
          icon: 'el-icon-mobile-phone'
        },
        {
          id: 3,
          title: '高性能',
          description: '优化的代码结构和高效的数据处理',
          icon: 'el-icon-lightning'
        }
      ]
    }
  },
  methods: {
    navigateToModule() {
      this.$router.push('/{{module_name}}')
    }
  }
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 2rem;
}

.card-title {
  font-size: 1.2rem;
  font-weight: bold;
}

.welcome-content {
  text-align: center;
  padding: 2rem;
}

.welcome-content p {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  color: #606266;
}

.features {
  margin-top: 2rem;
}

.feature-card {
  text-align: center;
  height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.feature-icon {
  font-size: 2rem;
  color: #409EFF;
  margin-bottom: 1rem;
}

.feature-card h3 {
  margin: 0.5rem 0;
  color: #303133;
}

.feature-card p {
  color: #606266;
  font-size: 0.9rem;
}
</style>
"""

# 通用CRUD页面组件模版
VUE_CRUD_COMPONENT = """
<template>
  <div class="{{component_name}}-page">
    <!-- 头部操作区 -->
    <el-card class="operation-card" shadow="never">
      <div slot="header" class="clearfix">
        <span class="card-title">{{module_title}}管理</span>
        <el-button style="float: right;" type="primary" @click="showAddDialog">
          <i class="el-icon-plus"></i> 添加{{entity_name}}
        </el-button>
      </div>
      
      <!-- 搜索表单 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        {{search_fields}}
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <i class="el-icon-search"></i> 搜索
          </el-button>
          <el-button @click="resetSearch">
            <i class="el-icon-refresh"></i> 重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
        :header-cell-style="{ background: '#f5f7fa' }"
      >
        {{table_columns}}
        <el-table-column label="操作" width="180" fixed="right">
          <template slot-scope="scope">
            <el-button size="mini" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button
              size="mini"
              type="danger"
              @click="handleDelete(scope.row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="pagination.current"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pagination.size"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
        >
        </el-pagination>
      </div>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      :title="dialogTitle"
      :visible.sync="dialogVisible"
      width="600px"
      @close="resetForm"
    >
      <el-form
        :model="form"
        :rules="rules"
        ref="form"
        label-width="100px"
      >
        {{form_fields}}
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitForm">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { {{api_methods}} } from '@/api/{{module_name}}'

export default {
  name: '{{ComponentName}}',
  data() {
    return {
      loading: false,
      tableData: [],
      dialogVisible: false,
      isEdit: false,
      searchForm: {{search_form_data}},
      form: {{form_data}},
      rules: {{validation_rules}},
      pagination: {
        current: 1,
        size: 10,
        total: 0
      }
    }
  },
  computed: {
    dialogTitle() {
      return this.isEdit ? '编辑{{entity_name}}' : '添加{{entity_name}}'
    }
  },
  mounted() {
    this.fetchData()
  },
  methods: {
    // 获取数据
    async fetchData() {
      this.loading = true
      try {
        const params = {
          ...this.searchForm,
          page: this.pagination.current,
          size: this.pagination.size
        }
        const response = await get{{EntityName}}List(params)
        this.tableData = response.data.records || []
        this.pagination.total = response.data.total || 0
      } catch (error) {
        this.$message.error('获取数据失败')
        console.error(error)
      } finally {
        this.loading = false
      }
    },

    // 搜索
    handleSearch() {
      this.pagination.current = 1
      this.fetchData()
    },

    // 重置搜索
    resetSearch() {
      this.searchForm = {{search_form_data}}
      this.handleSearch()
    },

    // 显示添加对话框
    showAddDialog() {
      this.isEdit = false
      this.dialogVisible = true
    },

    // 编辑
    handleEdit(row) {
      this.isEdit = true
      this.form = { ...row }
      this.dialogVisible = true
    },

    // 删除
    async handleDelete(row) {
      try {
        await this.$confirm('确认删除这条记录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await delete{{EntityName}}(row.id)
        this.$message.success('删除成功')
        this.fetchData()
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('删除失败')
          console.error(error)
        }
      }
    },

    // 提交表单
    async submitForm() {
      try {
        await this.$refs.form.validate()
        
        if (this.isEdit) {
          await update{{EntityName}}(this.form.id, this.form)
          this.$message.success('更新成功')
        } else {
          await create{{EntityName}}(this.form)
          this.$message.success('创建成功')
        }
        
        this.dialogVisible = false
        this.fetchData()
      } catch (error) {
        this.$message.error(this.isEdit ? '更新失败' : '创建失败')
        console.error(error)
      }
    },

    // 重置表单
    resetForm() {
      this.$refs.form && this.$refs.form.resetFields()
      this.form = {{form_data}}
    },

    // 分页
    handleSizeChange(val) {
      this.pagination.size = val
      this.fetchData()
    },

    handleCurrentChange(val) {
      this.pagination.current = val
      this.fetchData()
    }
  }
}
</script>

<style scoped>
.{{component_name}}-page {
  padding: 20px;
}

.operation-card {
  margin-bottom: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: bold;
}

.search-form {
  margin-top: 20px;
}

.table-card {
  background: white;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.dialog-footer {
  text-align: right;
}
</style>
"""

# API服务模版
VUE_API_SERVICE = """
import request from '@/utils/request'

// {{module_title}} API

/**
 * 获取{{entity_name}}列表
 * @param {Object} params 查询参数
 */
export function get{{EntityName}}List(params) {
  return request({
    url: '/api/{{api_prefix}}',
    method: 'get',
    params
  })
}

/**
 * 获取{{entity_name}}详情
 * @param {number|string} id {{entity_name}}ID
 */
export function get{{EntityName}}Detail(id) {
  return request({
    url: `/api/{{api_prefix}}/${id}`,
    method: 'get'
  })
}

/**
 * 创建{{entity_name}}
 * @param {Object} data {{entity_name}}数据
 */
export function create{{EntityName}}(data) {
  return request({
    url: '/api/{{api_prefix}}',
    method: 'post',
    data
  })
}

/**
 * 更新{{entity_name}}
 * @param {number|string} id {{entity_name}}ID
 * @param {Object} data {{entity_name}}数据
 */
export function update{{EntityName}}(id, data) {
  return request({
    url: `/api/{{api_prefix}}/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除{{entity_name}}
 * @param {number|string} id {{entity_name}}ID
 */
export function delete{{EntityName}}(id) {
  return request({
    url: `/api/{{api_prefix}}/${id}`,
    method: 'delete'
  })
}
"""

# HTTP请求工具模版
VUE_REQUEST_UTIL = """
import axios from 'axios'
import { Message, MessageBox } from 'element-ui'
import store from '@/store'
import { getToken } from '@/utils/auth'

// 创建axios实例
const service = axios.create({
  baseURL: process.env.VUE_APP_BASE_API || '/api',
  timeout: 10000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 在请求发送之前做一些处理
    if (store.getters.token) {
      // 让每个请求携带自定义token
      config.headers['Authorization'] = 'Bearer ' + getToken()
    }
    return config
  },
  error => {
    // 请求错误处理
    console.log(error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data

    // 如果自定义状态码不是200，则判断为错误
    if (res.code !== 200) {
      Message({
        message: res.message || 'Error',
        type: 'error',
        duration: 5 * 1000
      })

      // 401: 未授权
      if (res.code === 401) {
        MessageBox.confirm(
          '登录状态已过期，您可以继续留在该页面，或者重新登录',
          '确定登出',
          {
            confirmButtonText: '重新登录',
            cancelButtonText: '取消',
            type: 'warning'
          }
        ).then(() => {
          store.dispatch('user/resetToken').then(() => {
            location.reload()
          })
        })
      }
      return Promise.reject(new Error(res.message || 'Error'))
    } else {
      return res
    }
  },
  error => {
    console.log('err' + error)
    Message({
      message: error.message,
      type: 'error',
      duration: 5 * 1000
    })
    return Promise.reject(error)
  }
)

export default service
"""

# 路由配置模版
VUE_ROUTER_CONFIG = """
import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '首页' }
  },
  {{route_definitions}}
  {
    path: '*',
    redirect: '/'
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - {{project_title}}`
  }
  next()
})

export default router
"""

# Vuex状态管理模版
VUE_STORE_CONFIG = """
import Vue from 'vue'
import Vuex from 'vuex'
import {{module_name}} from './modules/{{module_name}}'

Vue.use(Vuex)

const store = new Vuex.Store({
  modules: {
    {{module_name}}
  },
  strict: process.env.NODE_ENV !== 'production'
})

export default store
"""

# 获取所有模版的函数
def get_all_frontend_templates():
    """获取所有前端模版"""
    return {
        'project_config': VUE_PROJECT_CONFIG,
        'vue_config': VUE_CONFIG_JS,
        'app_component': VUE_APP_COMPONENT,
        'home_component': VUE_HOME_COMPONENT,
        'crud_component': VUE_CRUD_COMPONENT,
        'api_service': VUE_API_SERVICE,
        'request_util': VUE_REQUEST_UTIL,
        'router_config': VUE_ROUTER_CONFIG,
        'store_config': VUE_STORE_CONFIG
    }

# 根据模版类型获取模版
def get_frontend_template(template_type: str) -> str:
    """根据模版类型获取模版"""
    templates = get_all_frontend_templates()
    return templates.get(template_type, "") 