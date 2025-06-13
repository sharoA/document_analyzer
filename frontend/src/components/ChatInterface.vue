<template>
  <div class="chat-container">
    <!-- 左侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2 class="app-title">
          <el-icon><ChatDotRound /></el-icon>
          analyDesign
        </h2>
        <el-button 
          type="primary" 
          @click="startNewChat"
          class="new-chat-btn"
        >
          新任务
        </el-button>
      </div>
      
      <div class="chat-history">
        <div class="history-section">
          <h3>需求文档智能分析</h3>
          <p class="section-subtitle">文档解析专家</p>
        </div>
        
        <div class="task-description">
          <h4>智能对话助手</h4>
          <p>专业的需求分析、访谈提纲生成和问卷设计助手</p>
          
          <div class="feature-tips">
            <p>💡 可以上传文档进行基于文档内容的智能对话</p>
            <p>📎 支持 Word、PDF、TXT、Markdown 格式文档</p>
          </div>
        </div>
      </div>

      <!-- 聊天消息区域 -->
      <div class="chat-messages" ref="messagesContainer">
        <div 
          v-for="message in messages" 
          :key="message.message_id"
          :class="['message', message.type]"
        >
          <div v-if="message.type === 'user'" class="user-message">
            <div class="message-content">{{ message.message }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
          
          <div v-else-if="message.type === 'chat_response'" class="bot-message">
            <div class="bot-avatar">
              <el-icon><User /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(message.message)"></div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
        </div>
        
        <div v-if="isTyping" class="typing-indicator">
          <div class="bot-avatar">
            <el-icon><User /></el-icon>
          </div>
          <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <div class="input-container">
          <!-- 隐藏的文件上传组件 -->
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :show-file-list="false"
            accept=".doc,.docx,.pdf,.txt,.md"
            style="display: none;"
          />
          
          <!-- 显示已上传的文件 -->
          <div v-if="uploadedFile" class="uploaded-file-card">
            <div class="file-card-header">
              <el-icon class="file-icon"><Document /></el-icon>
              <span class="file-name">{{ uploadedFile.name }}</span>
              <el-button 
                type="text" 
                size="small" 
                @click="removeFile"
                class="close-btn"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div class="file-card-footer">
              <span class="file-size">{{ formatFileSize(uploadedFile.size) }}</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="analyzeDocument"
                :loading="isAnalyzing"
                class="analyze-btn"
              >
                <el-icon><Promotion /></el-icon>
                开始文档解析
              </el-button>
            </div>
          </div>
          
          <el-input
            v-model="currentMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题或需求..."
            @keydown.ctrl.enter="sendMessage"
            :disabled="isTyping"
            resize="none"
          />
                      <div class="input-actions">
            <el-button-group>
              <el-button size="small" @click="attachFile">
                <el-icon><Paperclip /></el-icon>
                附件
              </el-button>
              <el-button size="small" @click="expandInput">
                <el-icon><FullScreen /></el-icon>
                展开
              </el-button>
            </el-button-group>
            <el-button 
              type="primary" 
              @click="sendMessage"
              :disabled="!currentMessage.trim() || isTyping"
              :loading="isTyping"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧 Agent 工作空间 -->
    <div class="agent-workspace">
      <!-- 工作空间头部 -->
      <div class="workspace-header">
        <h3>Agent 的工作空间</h3>
        <div class="connection-status">
          <el-tag 
            :type="connectionStatusType" 
            size="small"
            effect="plain"
          >
            <el-icon><Connection /></el-icon>
            {{ connectionStatusText }}
          </el-tag>
        </div>
      </div>

      <!-- Tab 导航 -->
      <el-tabs v-model="activeTab" class="workspace-tabs">
        <!-- 实时处理状态 -->
        <el-tab-pane label="实时跟随" name="realtime">
          <div class="tab-content">
            <div class="status-header">
              <h4>处理状态</h4>
              <el-tag :type="processingStatus.type" size="small">
                {{ processingStatus.text }}
              </el-tag>
            </div>
            
            <div class="processing-steps">
              <el-timeline>
                <el-timeline-item
                  v-for="step in processingSteps"
                  :key="step.id"
                  :type="step.status"
                  :timestamp="step.timestamp"
                >
                  <div class="step-content">
                    <h5>{{ step.title }}</h5>
                    <p>{{ step.description }}</p>
                    <div v-if="step.progress !== undefined" class="step-progress">
                      <el-progress 
                        :percentage="step.status === 'success' ? 100 : step.progress" 
                        :status="step.status === 'success' ? 'success' : undefined"
                      />
                    </div>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>
            
            <div v-if="currentProcessing" class="current-processing">
              <el-card>
                <template #header>
                  <div class="card-header">
                    <span>当前处理</span>
                    <el-icon class="rotating"><Loading /></el-icon>
                  </div>
                </template>
                <p>{{ currentProcessing }}</p>
              </el-card>
            </div>
          </div>
        </el-tab-pane>

        <!-- 上传文档预览 -->
        <el-tab-pane label="上传文档预览" name="preview">
          <div class="tab-content">
            <div v-if="!uploadedFile" class="empty-state">
              <el-empty description="暂无上传文档">
                <el-button type="primary" @click="attachFile">
                  <el-icon><Paperclip /></el-icon>
                  上传文档
                </el-button>
              </el-empty>
            </div>
            
            <div v-else class="document-preview">
              <div class="preview-header">
                <h4>{{ getPreviewTitle(uploadedFile) }}</h4>
                <div class="file-info">
                  <el-tag size="small" type="success">
                    <el-icon><Document /></el-icon>
                    {{ uploadedFile.name }}
                  </el-tag>
                  <span class="file-size">{{ formatFileSize(uploadedFile.size) }}</span>
                </div>
              </div>
              
              <div class="preview-content">
                <!-- 文档基本信息 -->
                <el-card style="margin-bottom: 16px;">
                  <template #header>
                    <div style="display: flex; align-items: center;">
                      <el-icon style="margin-right: 8px;"><Document /></el-icon>
                      <span>文档信息</span>
                    </div>
                  </template>
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="文件名">
                      {{ uploadedFile.name }}
                    </el-descriptions-item>
                    <el-descriptions-item label="文件大小">
                      {{ formatFileSize(uploadedFile.size) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="文件类型">
                      {{ getFileType(uploadedFile) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="扩展名">
                      {{ getFileExtension(uploadedFile.name) }}
                    </el-descriptions-item>
                  </el-descriptions>
                </el-card>
                
                <!-- 文档预览区域 -->
                <el-card>
                  <template #header>
                    <div style="display: flex; align-items: center;">
                      <el-icon style="margin-right: 8px;"><View /></el-icon>
                      <span>文档预览</span>
                    </div>
                  </template>
                  
                  <!-- 使用DocumentPreview组件 -->
                  <DocumentPreview :file="uploadedFile" />
                </el-card>
                
                <!-- 操作按钮 -->
                <div style="margin-top: 24px; text-align: center; padding: 20px; border-top: 1px solid #e4e7ed;">
                  <el-button size="large" @click="analyzeDocument" :loading="isAnalyzing">
                    <el-icon><Promotion /></el-icon>
                    开始分析文档
                  </el-button>
                  <el-button size="large" @click="removeFile">
                    <el-icon><Close /></el-icon>
                    移除文档
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 文件解析结果 -->
        <el-tab-pane label="解析结果" name="files">
          <div class="tab-content">
            <div v-if="!analysisResult" class="empty-state">
              <el-empty description="暂无解析结果">
                <el-button v-if="!uploadedFile" type="primary" @click="activeTab = 'preview'">
                  上传文档开始分析
                </el-button>
                <el-button v-else type="primary" size="large" @click="analyzeDocument" :loading="isAnalyzing">
                  <el-icon><Promotion /></el-icon>
                  开始分析文档
                </el-button>
              </el-empty>
            </div>
            
            <div v-else class="analysis-result">
              <div class="result-header">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                  <div>
                    <div class="result-title">
                      <h4>{{  getAnalysisFileName() || '📄 文档解析结果' }}</h4>
                    </div>
                    <div class="result-meta">
                      <el-tag size="small" :type="getResultTypeTag(analysisResult.type)">
                        {{ getResultTypeText(analysisResult.type) }}
                      </el-tag>
                      <span class="result-time">{{ formatTime(analysisResult.timestamp) }}</span>
                    </div>
                  </div>
                  <el-button v-if="uploadedFile" type="primary" size="small" @click="analyzeDocument" :loading="isAnalyzing">
                    <el-icon><Promotion /></el-icon>
                    重新分析
                  </el-button>
                </div>
              </div>
              
              <!-- 分析结果显示区域 -->
              <div class="results-container">
                <el-scrollbar height="100%" class="analysis-scrollbar">
                  <div class="result-content">
                  <!-- 文件基本信息 -->
                  <el-card class="info-card" v-if="analysisResult">
                    <template #header>
                      <h5>当前文件基本信息</h5>
                    </template>
                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item label="文件名称">
                        {{ getAnalysisFileName() }}
                      </el-descriptions-item>
                      <el-descriptions-item label="文件类型">
                        {{ getAnalysisFileType() }}
                        
                      </el-descriptions-item>
                      <el-descriptions-item label="子类型">
                        {{ analysisResult.fileFormat.subType || '未知' }}
                      </el-descriptions-item>
                      <el-descriptions-item label="文件大小">
                        {{ uploadedFile ? formatFileSize(uploadedFile.size) : formatFileSize(analysisResult.fileFormat.basicInfo?.fileSize || 0) }}
                      </el-descriptions-item>
                      <el-descriptions-item label="字符数">
                        {{ getAnalysisCharacterCount() }}
                      </el-descriptions-item>
                    </el-descriptions>
                  </el-card>


                  <!-- 文档结构摘要 -->
                  <el-card class="info-card" v-if="analysisResult && analysisResult.documentStructure?.contentSummary">
                    <template #header>
                      <h5>📋 文档结构摘要</h5>
                    </template>
                    <div class="document-summary">
                      <!-- 摘要 -->
                      <div class="summary-section" v-if="analysisResult.documentStructure.contentSummary.abstract">
                        <h6>文档摘要</h6>
                        <p class="abstract-text">{{ analysisResult.documentStructure.contentSummary.abstract }}</p>
                      </div>
                      
                      <!-- 功能统计 -->
                      <el-descriptions :column="2" border size="small" style="margin-bottom: 16px;">
                        <el-descriptions-item label="功能数量">
                          {{ analysisResult.documentStructure.contentSummary.functionCount || 0 }}
                        </el-descriptions-item>
                        <el-descriptions-item label="API数量">
                          {{ analysisResult.documentStructure.contentSummary.apiCount || 0 }}
                        </el-descriptions-item>
                        <el-descriptions-item label="数据库变更">
                          {{ analysisResult.documentStructure.contentSummary.dbChangeCount || 0 }}
                        </el-descriptions-item>
                        <el-descriptions-item label="消息队列">
                          {{ analysisResult.documentStructure.contentSummary.mqCount || 0 }}
                        </el-descriptions-item>
                        <el-descriptions-item label="定时器">
                          {{ analysisResult.documentStructure.contentSummary.timerCount || 0 }}
                        </el-descriptions-item>
                      </el-descriptions>

                      <!-- 功能列表 -->
                      <div class="function-list" v-if="analysisResult.documentStructure.contentSummary.functionName && analysisResult.documentStructure.contentSummary.functionName.length > 0">
                        <h6>功能列表</h6>
                        <el-tag v-for="(func, index) in analysisResult.documentStructure.contentSummary.functionName" 
                               :key="index" 
                               type="primary" 
                               size="small" 
                               style="margin: 2px 4px 2px 0;">
                          {{ func }}
                        </el-tag>
                      </div>

                      <!-- API列表 -->
                      <div class="api-list" v-if="analysisResult.documentStructure.contentSummary.apiName && analysisResult.documentStructure.contentSummary.apiName.length > 0">
                        <h6>API列表</h6>
                        <el-tag v-for="(api, index) in analysisResult.documentStructure.contentSummary.apiName" 
                               :key="index" 
                               type="success" 
                               size="small" 
                               style="margin: 2px 4px 2px 0;">
                          {{ api }}
                        </el-tag>
                      </div>
                    </div>
                  </el-card>

                  <!-- 关键词分析 -->
                  <el-card class="info-card" v-if="analysisResult && analysisResult.documentStructure?.contentKeyWord">
                    <template #header>
                      <h5>🔍 关键词分析</h5>
                    </template>
                    <div class="keyword-analysis">
                      <!-- 基础关键词 -->
                      <div class="keywords-section" v-if="analysisResult.documentStructure.contentKeyWord.keywords">
                        <h6>基础关键词</h6>
                        <el-tag v-for="(keyword, index) in analysisResult.documentStructure.contentKeyWord.keywords" 
                               :key="index" 
                               size="small" 
                               style="margin: 2px 4px 2px 0;">
                          {{ keyword }}
                        </el-tag>
                      </div>

                      <!-- 主要关键词详情 -->
                      <div class="primary-keywords" v-if="analysisResult.documentStructure.contentKeyWord.primaryKeywords">
                        <h6>主要关键词详情</h6>
                        <el-table :data="analysisResult.documentStructure.contentKeyWord.primaryKeywords" 
                                 size="small" 
                                 style="width: 100%">
                          <el-table-column prop="keyword" label="关键词" width="100"/>
                          <el-table-column prop="frequency" label="频次" width="60"/>
                          <el-table-column prop="importance" label="重要度" width="80">
                            <template #default="scope">
                              {{ (parseFloat(scope.row.importance) * 100).toFixed(0) }}%
                            </template>
                          </el-table-column>
                          <el-table-column prop="positions" label="出现位置" min-width="120">
                            <template #default="scope">
                              <el-tag v-for="(pos, index) in scope.row.positions" 
                                     :key="index" 
                                     size="mini" 
                                     type="info"
                                     style="margin: 1px;">
                                {{ pos }}
                              </el-tag>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>

                      <!-- 语义聚类 -->
                      <div class="semantic-clusters" v-if="analysisResult.documentStructure.contentKeyWord.semanticClusters">
                        <h6>语义聚类</h6>
                        <div v-for="(cluster, index) in analysisResult.documentStructure.contentKeyWord.semanticClusters" 
                             :key="index" 
                             class="cluster-item">
                          <div class="cluster-header">
                            <span class="cluster-name">{{ cluster.clusterName }}</span>
                            <el-tag size="mini" type="warning">
                              相关度: {{ (parseFloat(cluster.coherenceScore) * 100).toFixed(0) }}%
                            </el-tag>
                          </div>
                          <div class="cluster-keywords">
                            <el-tag v-for="(keyword, kidx) in cluster.keywords" 
                                   :key="kidx" 
                                   size="mini" 
                                   style="margin: 2px;">
                              {{ keyword }}
                            </el-tag>
                          </div>
                        </div>
                      </div>
                    </div>
                  </el-card>

                  <!-- 元数据信息 -->
                  <el-card class="info-card" v-if="analysisResult && analysisResult.documentStructure?.metadata">
                    <template #header>
                      <h5>👥 元数据信息</h5>
                    </template>
                    <el-descriptions :column="1" border size="small">
                      <el-descriptions-item label="用户角色" v-if="analysisResult.documentStructure.metadata.userRole">
                        <el-tag v-for="(role, index) in analysisResult.documentStructure.metadata.userRole" 
                               :key="index" 
                               type="primary" 
                               size="small" 
                               style="margin: 2px 4px 2px 0;">
                          {{ role }}
                        </el-tag>
                      </el-descriptions-item>
                      <el-descriptions-item label="目标受众" v-if="analysisResult.documentStructure.metadata.targetAudience">
                        <el-tag v-for="(audience, index) in analysisResult.documentStructure.metadata.targetAudience" 
                               :key="index" 
                               type="success" 
                               size="small" 
                               style="margin: 2px 4px 2px 0;">
                          {{ audience }}
                        </el-tag>
                      </el-descriptions-item>
                    </el-descriptions>
                  </el-card>

                  <!-- 解析状态 -->
                  <el-card class="info-card" v-if="analysisResult">
                    <template #header>
                      <h5>✅ 解析状态</h5>
                    </template>
                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item label="解析状态">
                        <el-tag type="success" size="small">解析完成</el-tag>
                      </el-descriptions-item>
                      <el-descriptions-item label="解析耗时">
                        {{ analysisResult.details?.parsing_duration?.toFixed(2) || '0.00' }} 秒
                      </el-descriptions-item>
                      <el-descriptions-item label="解析备注" span="2" v-if="analysisResult.notes">
                        {{ analysisResult.notes }}
                      </el-descriptions-item>
                    </el-descriptions>
                  </el-card>
                  
                  <!-- 内容分析结果 -->
                  <el-card class="info-card" v-if="analysisResult.contentAnalysis">
                    <template #header>
                      <h5>内容分析结果</h5>
                    </template>
                    <div class="content-analysis-result">
                      
                      <!-- 需求分析（如果是需求文档） -->
                      <div v-if="analysisResult.contentAnalysis.requirements_analysis" class="analysis-section">
                        <h6>需求分析</h6>
                        <el-descriptions :column="1" border size="small">
                          <el-descriptions-item label="功能需求数">
                            {{ analysisResult.contentAnalysis.requirements_analysis.functional_requirements?.length || 0 }}
                          </el-descriptions-item>
                          <el-descriptions-item label="非功能需求数">
                            {{ analysisResult.contentAnalysis.requirements_analysis.non_functional_requirements?.length || 0 }}
                          </el-descriptions-item>
                          <el-descriptions-item label="优先级提及">
                            {{ analysisResult.contentAnalysis.requirements_analysis.priority_mentions?.length || 0 }}
                          </el-descriptions-item>
                        </el-descriptions>
                      </div>
                    </div>
                  </el-card>
                  
                  <!-- AI分析结果 -->
                  <el-card class="info-card" v-if="analysisResult.aiAnalysis">
                    <template #header>
                      <div class="ai-analysis-header">
                        <h5>智能处理结果</h5>
                        <el-tag size="small" type="success">
                          {{ analysisResult.aiAnalysis.analysis_type || '全面分析' }}
                        </el-tag>
                      </div>
                    </template>
                    <div class="ai-analysis-result">
                      <!-- AI分析信息 -->
                      <el-descriptions :column="2" border size="small" style="margin-bottom: 16px;">
                        <el-descriptions-item label="分析模型">
                          {{ analysisResult.aiAnalysis.analysis_model || 'Doubao' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="置信度">
                          {{ ((analysisResult.aiAnalysis.confidence_score || 0.95) * 100).toFixed(1) }}%
                        </el-descriptions-item>
                        <el-descriptions-item label="分析时间">
                          {{ formatTime(analysisResult.aiAnalysis.analyzed_at || Date.now()) }}
                        </el-descriptions-item>
                        <el-descriptions-item label="分析耗时">
                          {{ analysisResult.aiAnalysis.analysis_duration?.toFixed(2) || '0.00' }} 秒
                        </el-descriptions-item>
                      </el-descriptions>
                      
                      <!-- AI分析内容 -->
                      <div class="ai-response-content">
                        <h6>智能分析报告</h6>
                        <div class="ai-response-text">
                          <el-scrollbar max-height="60vh" class="ai-content-scrollbar">
                            <div v-if="analysisResult.aiAnalysis.ai_response" v-html="formatAIResponse(analysisResult.aiAnalysis.ai_response)"></div>
                            <div v-else class="no-content">{{ analysisResult.aiAnalysis.ai_response || '分析完成' }}</div>
                          </el-scrollbar>
                        </div>
                      </div>
                    </div>
                  </el-card>
                  
                  <!-- Markdown分析报告 -->
                  <el-card class="info-card" v-if="analysisResult.markdownContent">
                    <template #header>
                      <div class="markdown-header">
                        <h5>📋 {{ getAnalysisFileName() }} - 分析报告</h5>
                        <el-button-group size="small">
                          <el-button @click="copyMarkdownContent">
                            <el-icon><DocumentCopy /></el-icon>
                            复制报告
                          </el-button>
                          <el-button @click="downloadMarkdownContent">
                            <el-icon><Download /></el-icon>
                            下载Markdown
                          </el-button>
                        </el-button-group>
                      </div>
                    </template>
                    <div class="markdown-content">
                      <el-scrollbar max-height="70vh" class="markdown-content-scrollbar">
                        <div class="markdown-preview" v-html="renderMarkdown(analysisResult.markdownContent)"></div>
                      </el-scrollbar>
                    </div>
                    
                    <!-- 移动到此处的操作按钮 -->
                    <div class="markdown-actions" style="margin-top: 16px; text-align: center; padding: 16px; border-top: 1px solid #e4e7ed;">
                      <el-button type="primary" @click="analyzeWithAI">
                        <el-icon><Promotion /></el-icon>
                        智能处理
                      </el-button>
                      <el-button @click="exportResult">
                        <el-icon><Download /></el-icon>
                        立即出结果
                      </el-button>
                      <el-button @click="clearResult">
                        <el-icon><Delete /></el-icon>
                        访问全结果
                      </el-button>
                    </div>
                  </el-card>
                  
                  <!-- 分析总结 -->
                  <el-card class="info-card" v-if="analysisResult.analysisSummary">
                    <template #header>
                      <div class="summary-header">
                        <h5>📝 {{ getAnalysisFileName() }} - 分析总结</h5>
                        <el-button-group size="small">
                          <el-button @click="copySummary">
                            <el-icon><DocumentCopy /></el-icon>
                            复制总结
                          </el-button>
                        </el-button-group>
                      </div>
                    </template>
                    <div class="summary-content">
                      <div class="summary-text" v-html="formatSummary(analysisResult.analysisSummary)"></div>
                    </div>
                  </el-card>
                  
                  <!-- 文档内容预览 -->
                  <el-card class="content-card" v-if="analysisResult.content">
                    <template #header>
                      <div class="content-header">
                        <h5>文档内容</h5>
                        <el-button-group size="small">
                          <el-button @click="copyContent">
                            <el-icon><DocumentCopy /></el-icon>
                            复制内容
                          </el-button>
                          <el-button @click="downloadContent">
                            <el-icon><Download /></el-icon>
                            下载文本
                          </el-button>
                        </el-button-group>
                      </div>
                    </template>
                    
                    <div class="content-preview">
                      <el-scrollbar max-height="50vh" class="document-content-scrollbar">
                        <pre class="content-text">{{ analysisResult.content }}</pre>
                      </el-scrollbar>
                    </div>
                  </el-card>
                  
                  <!-- Word文档特有信息 -->
                  <el-card 
                    class="info-card" 
                    v-if="analysisResult.details?.type === 'word' && analysisResult.details.tables?.length"
                  >
                    <template #header>
                      <h5>表格内容</h5>
                    </template>
                    <div class="tables-content">
                      <div 
                        v-for="(table, index) in analysisResult.details.tables" 
                        :key="index"
                        class="table-item"
                      >
                        <h6>表格 {{ index + 1 }}</h6>
                        <el-table :data="formatTableData(table)" border size="small">
                          <el-table-column 
                            v-for="(col, colIndex) in getTableColumns(table)" 
                            :key="colIndex"
                            :prop="`col${colIndex}`"
                            :label="`列${colIndex + 1}`"
                            show-overflow-tooltip
                          />
                        </el-table>
                      </div>
                    </div>
                  </el-card>
                  
                  <!-- PDF文档特有信息 -->
                  <el-card 
                    class="info-card" 
                    v-if="analysisResult.details?.type === 'pdf' && analysisResult.details.pages?.length"
                  >
                    <template #header>
                      <h5>页面内容</h5>
                    </template>
                    <div class="pages-content">
                      <el-collapse>
                        <el-collapse-item 
                          v-for="page in analysisResult.details.pages" 
                          :key="page.page_number"
                          :title="`第 ${page.page_number} 页`"
                          :name="page.page_number"
                        >
                          <div class="page-content">
                            <div v-if="page.error" class="page-error">
                              <el-alert 
                                :title="`第${page.page_number}页解析失败`"
                                type="warning"
                                :description="page.error"
                                show-icon
                                :closable="false"
                              />
                            </div>
                            <pre v-else class="page-text">{{ page.text || '该页面无文本内容' }}</pre>
                          </div>
                        </el-collapse-item>
                      </el-collapse>
                    </div>
                  </el-card>
                  
                  </div>
                </el-scrollbar>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 导出功能 -->
        <el-tab-pane label="终端" name="export">
          <div class="tab-content">
            <div class="export-options">
              <h4>导出选项</h4>
              
              <el-card class="export-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><Document /></el-icon>
                    <span>分析报告</span>
                  </div>
                </template>
                <p>导出完整的需求分析报告，包含所有分析结果和建议</p>
                <div class="export-actions">
                  <el-button-group>
                    <el-button @click="exportReport('pdf')" :disabled="!analysisResult">
                      <el-icon><Download /></el-icon>
                      PDF
                    </el-button>
                    <el-button @click="exportReport('word')" :disabled="!analysisResult">
                      <el-icon><Download /></el-icon>
                      Word
                    </el-button>
                    <el-button @click="exportReport('markdown')" :disabled="!analysisResult">
                      <el-icon><Download /></el-icon>
                      Markdown
                    </el-button>
                  </el-button-group>
                </div>
              </el-card>
              
              <el-card class="export-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><ChatDotRound /></el-icon>
                    <span>对话记录</span>
                  </div>
                </template>
                <p>导出完整的对话记录和交互历史</p>
                <div class="export-actions">
                  <el-button @click="exportChat()" :disabled="messages.length === 0">
                    <el-icon><Download /></el-icon>
                    导出对话
                  </el-button>
                </div>
              </el-card>
              
              <el-card class="export-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><Setting /></el-icon>
                    <span>自定义导出</span>
                  </div>
                </template>
                <p>选择特定内容进行导出</p>
                <div class="custom-export">
                  <el-checkbox-group v-model="exportOptions">
                    <el-checkbox label="basicInfo">基本信息</el-checkbox>
                    <el-checkbox label="clientInfo">需求方信息</el-checkbox>
                    <el-checkbox label="analysis">详细分析</el-checkbox>
                    <el-checkbox label="suggestions">建议和改进</el-checkbox>
                    <el-checkbox label="chat">对话记录</el-checkbox>
                  </el-checkbox-group>
                  <el-button 
                    type="primary" 
                    @click="exportCustom()" 
                    :disabled="exportOptions.length === 0"
                    style="margin-top: 10px;"
                  >
                    <el-icon><Download /></el-icon>
                    自定义导出
                  </el-button>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useWebSocketStore } from '../stores/websocket'
import { 
  ChatDotRound, 
  User, 
  Connection, 
  Microphone, 
  Document, 
  Check,
  Loading, 
  Promotion,
  Close,
  Paperclip,
  FullScreen,
  Setting,
  Download,
  View,
  InfoFilled,
  ArrowLeft,
  ArrowRight,
  ZoomIn,
  ZoomOut,
  DocumentCopy,
  Delete
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DocumentPreview from './DocumentPreview.vue'
import MarkdownIt from 'markdown-it'

// 响应式数据
const currentMessage = ref('')
const messagesContainer = ref(null)
const uploadRef = ref(null)
const uploadedFile = ref(null)
const isAnalyzing = ref(false)
const isTyping = ref(false)
const isSending = ref(false)
const showRightPanel = ref(false)
const activeTab = ref('realtime')
const exportOptions = ref([])

// WebSocket store
const wsStore = useWebSocketStore()

// 计算属性
const messages = computed(() => wsStore.messages)
const isConnected = computed(() => wsStore.isConnected)
const connectionStatus = computed(() => wsStore.connectionStatus)
const processingStatus = computed(() => ({
  type: wsStore.isProcessing ? 'warning' : 'success',
  text: wsStore.isProcessing ? '处理中...' : '就绪'
}))
const processingSteps = computed(() => wsStore.processingSteps || [])
const currentProcessing = computed(() => wsStore.currentProcessing)
const analysisResult = computed(() => wsStore.analysisResult)
// 监听 analysisResult 变化并打印
watch(analysisResult, (newValue) => {
  console.log('📊 Analysis Result:', newValue)
}, { deep: true })

const connectionStatusType = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return 'success'
    case 'connecting': return 'warning'
    case 'disconnected': return 'danger'
    default: return 'info'
  }
})

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return '已连接'
    case 'connecting': return '连接中'
    case 'disconnected': return '已断开'
    default: return '未知状态'
  }
})

const parsingStatusType = computed(() => {
  switch (wsStore.parsingStatus) {
    case 'uploading': return 'warning'
    case 'parsing': return 'primary'
    case 'content_analyzing': return 'primary'
    case 'ai_analyzing': return 'primary'
    case 'completed': return 'success'
    case 'failed': return 'danger'
    default: return 'info'
  }
})

const parsingStatusText = computed(() => {
  switch (wsStore.parsingStatus) {
    case 'idle': return '待解析'
    case 'uploading': return '上传中'
    case 'parsing': return '文档解析中'
    case 'content_analyzing': return '内容分析中'
    case 'ai_analyzing': return '智能处理中'
    case 'completed': return '解析完成'
    case 'failed': return '解析失败'
    default: return '未知状态'
  }
})

// 方法
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatTime = (timestamp) => {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } catch (error) {
    return ''
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getFileType = (file) => {
  const typeMap = {
    'application/msword': 'Microsoft Word 文档',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Microsoft Word 文档',
    'application/pdf': 'PDF 文档',
    'text/plain': '纯文本文档',
    'text/markdown': 'Markdown 文档'
  }
  return typeMap[file.type] || '未知文档类型'
}

const getFileExtension = (fileName) => {
  const lastDot = fileName.lastIndexOf('.')
  return lastDot !== -1 ? fileName.substring(lastDot) : '无扩展名'
}

const getPreviewTitle = (file) => {
  return '文档预览'
}

const formatMessage = (message) => {
  return message
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isTyping.value) return
  
  const message = currentMessage.value.trim()
  currentMessage.value = ''
  isTyping.value = true
  
  try {
    await wsStore.sendMessage(message)
  } catch (error) {
    ElMessage.error('发送消息失败: ' + error.message)
  } finally {
    isTyping.value = false
  }
}

const startNewChat = () => {
  wsStore.clearMessages()
  uploadedFile.value = null
  activeTab.value = 'realtime'
  ElMessage.success('已开始新任务')
}

const toggleRealtime = () => {
  ElMessage.info('实时问答功能开发中...')
}

const showFiles = () => {
  activeTab.value = 'files'
}

const attachFile = () => {
  // 触发隐藏的文件上传组件
  const fileInput = uploadRef.value?.$el.querySelector('input[type="file"]')
  if (fileInput) {
    fileInput.click()
  }
}

const expandInput = () => {
  ElMessageBox.prompt('请输入详细内容', '展开输入', {
    inputType: 'textarea',
    inputValue: currentMessage.value,
    inputPlaceholder: '请输入您的问题或需求...'
  }).then(({ value }) => {
    currentMessage.value = value
  }).catch(() => {
    // 用户取消
  })
}

// 文件上传相关方法
const handleFileChange = (file) => {
  console.log('文件上传开始:', file)
  
  const allowedTypes = [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/pdf',
    'text/plain',
    'text/markdown'
  ]
  
  console.log('文件类型:', file.raw.type)
  console.log('文件名:', file.name)
  console.log('文件大小:', file.size)
  
  // 检查文件类型
  if (!allowedTypes.includes(file.raw.type) && !file.name.match(/\.(doc|docx|pdf|txt|md)$/i)) {
    ElMessage.error('不支持的文件格式，请上传 Word、PDF、TXT 或 Markdown 文件')
    return false
  }
  
  // 检查文件大小（21MB限制）
  const maxFileSize = 21 * 1024 * 1024 // 21MB
  if (file.raw.size > maxFileSize) {
    const fileSizeMB = (file.raw.size / (1024 * 1024)).toFixed(1)
    ElMessage.error(`文件大小 ${fileSizeMB}MB 超过限制，最大允许 21MB`)
    return false
  }
  
  // 存储原始的File对象，而不是Element Plus的包装对象
  uploadedFile.value = file.raw
  console.log('uploadedFile设置完成:', uploadedFile.value)
  
  // 使用nextTick确保DOM更新后再切换页签
  nextTick(() => {
    console.log('切换到预览页签...')
    activeTab.value = 'preview'
    console.log('当前活动页签:', activeTab.value)
    
    // 强制触发响应式更新
    setTimeout(() => {
      console.log('延迟检查 - 当前页签:', activeTab.value)
      console.log('延迟检查 - 上传文件:', uploadedFile.value?.name)
    }, 100)
  })
  
  const fileSizeMB = (file.raw.size / (1024 * 1024)).toFixed(1)
  ElMessage.success(`文件 ${file.name} (${fileSizeMB}MB) 已选择，点击"开始分析"进行处理`)
}

const removeFile = () => {
  uploadedFile.value = null
  uploadRef.value?.clearFiles()
}

const analyzeDocument = async () => {
  if (!uploadedFile.value) {
    ElMessage.warning('请先上传文档')
    return
  }
  
  isAnalyzing.value = true
  activeTab.value = 'realtime'
  
  try {
    // 清空之前的处理步骤
    wsStore.clearProcessingSteps()
    wsStore.resetParsingState()
    
    // 添加文档上传完成步骤
    wsStore.updateProcessingStep({
      id: 'step_upload',
      title: '文档上传',
      description: `文件上传完成: ${uploadedFile.value.name}`,
      status: 'success',
      timestamp: new Date().toLocaleTimeString(),
      progress: 100
    })
    
    // 使用V2版本的完整分析流程
    const result = await wsStore.startFullAnalysisV2(uploadedFile.value)
    
    if (result.success) {
      ElMessage.success('完整分析流程已启动，请查看实时进度')
      
      // 监听解析状态变化
      const checkStatus = () => {
        if (wsStore.parsingStatus === 'completed') {
          ElMessage.success('完整分析完成')
          activeTab.value = 'files'
          isAnalyzing.value = false
        } else if (wsStore.parsingStatus === 'failed') {
          ElMessage.error('分析失败')
          isAnalyzing.value = false
        } else if (wsStore.isFileProcessing) {
          // 继续监听
          setTimeout(checkStatus, 1000)
        } else {
          isAnalyzing.value = false
        }
      }
      
      checkStatus()
    } else {
      throw new Error(result.error || '启动分析失败')
    }
    
  } catch (error) {
    ElMessage.error('分析启动失败: ' + error.message)
    isAnalyzing.value = false
    
    // 添加失败步骤
    wsStore.updateProcessingStep({
      id: 'step_parsing_failed',
      title: '解析失败',
      description: `解析失败: ${error.message}`,
      status: 'danger',
      timestamp: new Date().toLocaleTimeString(),
      progress: 0
    })
  }
}

// 导出功能
const exportReport = async (format) => {
  if (!analysisResult.value) {
    ElMessage.warning('暂无分析结果可导出')
    return
  }
  
  try {
    // 这里应该调用后端API进行导出
    ElMessage.success(`正在导出 ${format.toUpperCase()} 格式的分析报告...`)
    
    // 模拟导出过程
    setTimeout(() => {
      ElMessage.success('导出完成')
    }, 2000)
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

const exportChat = async () => {
  if (messages.value.length === 0) {
    ElMessage.warning('暂无对话记录可导出')
    return
  }
  
  try {
    const chatContent = messages.value.map(msg => {
      const time = formatTime(msg.timestamp)
      const sender = msg.type === 'user' ? '用户' : 'AI助手'
      return `[${time}] ${sender}: ${msg.message}`
    }).join('\n')
    
    const blob = new Blob([chatContent], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `对话记录_${new Date().toLocaleDateString()}.txt`
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('对话记录导出完成')
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

const exportCustom = async () => {
  if (exportOptions.value.length === 0) {
    ElMessage.warning('请选择要导出的内容')
    return
  }
  
  try {
    let content = '# 自定义导出报告\n\n'
    
    if (exportOptions.value.includes('basicInfo') && analysisResult.value?.basicInfo) {
      content += '## 基本信息\n'
      Object.entries(analysisResult.value.basicInfo).forEach(([key, value]) => {
        content += `- ${key}: ${value}\n`
      })
      content += '\n'
    }
    
    if (exportOptions.value.includes('clientInfo') && analysisResult.value?.clientInfo) {
      content += '## 需求方信息\n'
      Object.entries(analysisResult.value.clientInfo).forEach(([key, value]) => {
        content += `- ${key}: ${value}\n`
      })
      content += '\n'
    }
    
    if (exportOptions.value.includes('analysis') && analysisResult.value?.analysis) {
      content += '## 详细分析\n'
      content += analysisResult.value.analysis.replace(/<[^>]*>/g, '') + '\n\n'
    }
    
    if (exportOptions.value.includes('suggestions') && analysisResult.value?.suggestions) {
      content += '## 建议和改进\n'
      analysisResult.value.suggestions.forEach(suggestion => {
        content += `- ${suggestion}\n`
      })
      content += '\n'
    }
    
    if (exportOptions.value.includes('chat') && messages.value.length > 0) {
      content += '## 对话记录\n'
      messages.value.forEach(msg => {
        const time = formatTime(msg.timestamp)
        const sender = msg.type === 'user' ? '用户' : 'AI助手'
        content += `**[${time}] ${sender}**: ${msg.message}\n\n`
      })
    }
    
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `自定义报告_${new Date().toLocaleDateString()}.md`
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('自定义导出完成')
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// 监听上传文件变化
watch(uploadedFile, (newFile, oldFile) => {
  console.log('uploadedFile变化:', { newFile, oldFile })
}, { deep: true })

// 监听活动页签变化
watch(activeTab, (newTab, oldTab) => {
  console.log('activeTab变化:', { newTab, oldTab })
})

// 组件挂载时初始化
onMounted(() => {
  scrollToBottom()
  console.log('组件已挂载')
  console.log('初始uploadedFile:', uploadedFile.value)
  console.log('初始activeTab:', activeTab.value)
  
  // 监听切换到结果页签的事件
  window.addEventListener('switchToResultsTab', handleSwitchToResultsTab)
})

// 事件处理函数
const handleSwitchToResultsTab = (event) => {
  const { tab } = event.detail
  if (tab) {
    activeTab.value = tab
    ElMessage.success('分析完成，已自动切换到解析结果页签')
  }
}

// 组件卸载时清理事件监听器
onUnmounted(() => {
  window.removeEventListener('switchToResultsTab', handleSwitchToResultsTab)
})

const getResultTypeTag = (type) => {
  switch (type) {
    case 'text': return 'primary'
    case 'word': return 'success'
    case 'pdf': return 'warning'
    default: return 'info'
  }
}

const getResultTypeText = (type) => {
  switch (type) {
    case 'text': return '文本文档'
    case 'word': return 'Word文档'
    case 'pdf': return 'PDF文档'
    default: return '文档解析'
  }
}

// 表格数据格式化
const formatTableData = (table) => {
  if (!table || !Array.isArray(table)) return []
  
  return table.map(row => {
    const rowData = {}
    row.forEach((cell, index) => {
      rowData[`col${index}`] = cell
    })
    return rowData
  })
}

const getTableColumns = (table) => {
  if (!table || !Array.isArray(table) || table.length === 0) return []
  return table[0] || []
}

// 内容操作方法
const copyContent = async () => {
  if (!analysisResult.value?.content) {
    ElMessage.warning('没有可复制的内容')
    return
  }
  
  try {
    await navigator.clipboard.writeText(analysisResult.value.content)
    ElMessage.success('内容已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const downloadContent = () => {
  if (!analysisResult.value?.content) {
    ElMessage.warning('没有可下载的内容')
    return
  }
  
  const fileName = getAnalysisFileName().replace(/\.[^/.]+$/, "") // 移除原文件扩展名
  const blob = new Blob([analysisResult.value.content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${fileName}_content.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('内容下载开始')
}

const analyzeWithAI = async () => {
  if (!analysisResult.value?.content) {
    ElMessage.warning('没有可分析的内容')
    return
  }
  
  try {
    const message = `请分析以下文档内容：\n\n${analysisResult.value.content.substring(0, 2000)}${analysisResult.value.content.length > 2000 ? '...' : ''}`
    await wsStore.sendMessage(message)
    activeTab.value = 'realtime'
    ElMessage.success('已发送给AI进行智能处理')
  } catch (error) {
    ElMessage.error('发送分析请求失败')
  }
}

const exportResult = () => {
  ElMessage.info('导出功能开发中...')
}

const clearResult = () => {
  wsStore.clearAnalysisResult()
  ElMessage.success('解析结果已清空')
}

// 新增的辅助方法
const getDocumentTypeText = (type) => {
  const typeMap = {
    'requirements': '需求文档',
    'design': '设计文档',
    'general': '通用文档'
  }
  return typeMap[type] || '未知类型'
}

const getLanguageText = (language) => {
  const languageMap = {
    'chinese': '中文',
    'english': '英文',
    'unknown': '未知语言'
  }
  return languageMap[language] || language
}

const getAnalysisTypeText = (type) => {
  const typeMap = {
    'comprehensive': '全面分析',
    'summary': '摘要分析',
    'requirements': '需求分析',
    'custom': '自定义分析'
  }
  return typeMap[type] || type
}

const formatAIResponse = (response) => {
  if (!response) return ''
  
  return response
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/#{1,6}\s*(.*?)(?=\n|$)/g, '<h6>$1</h6>')
    .replace(/^\d+\.\s*(.*?)(?=\n|$)/gm, '<li>$1</li>')
    .replace(/^-\s*(.*?)(?=\n|$)/gm, '<li>$1</li>')
}

// 创建markdown渲染器实例
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

// Markdown渲染方法
const renderMarkdown = (content) => {
  if (!content) return ''
  return md.render(content)
}

// Markdown操作方法
const copyMarkdownContent = async () => {
  if (!analysisResult.value?.markdownContent) {
    ElMessage.warning('没有可复制的报告内容')
    return
  }
  
  try {
    await navigator.clipboard.writeText(analysisResult.value.markdownContent)
    ElMessage.success('分析报告已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const downloadMarkdownContent = () => {
  if (!analysisResult.value?.markdownContent) {
    ElMessage.warning('没有可下载的报告内容')
    return
  }
  
  const fileName = getAnalysisFileName().replace(/\.[^/.]+$/, "") // 移除原文件扩展名
  const blob = new Blob([analysisResult.value.markdownContent], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${fileName}_analysis_report.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('分析报告下载开始')
}

const formatSummary = (summary) => {
  if (!summary) return ''
  return summary.replace(/\n/g, '<br>')
}

const copySummary = async () => {
  if (!analysisResult.value?.analysisSummary) {
    ElMessage.warning('没有可复制的总结内容')
    return
  }
  
  try {
    await navigator.clipboard.writeText(analysisResult.value.analysisSummary)
    ElMessage.success('总结已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const getAnalysisFileName = () => {
  // 优先使用后端返回的fileFormat.fileName
  return analysisResult.value?.fileFormat?.fileName || 
         analysisResult.value?.fileInfo?.name || 
         '未知文件'
}

const getAnalysisFileType = () => {
  return analysisResult.value?.fileInfo?.type || analysisResult.value?.details?.type || '未知类型'
}

const getAnalysisFileSize = () => {
  return formatFileSize(analysisResult.value?.fileInfo?.size || 0)
}

const getAnalysisCharacterCount = () => {
  return analysisResult.value?.contentAnalysis?.statistics?.character_count || 
         analysisResult.value?.details?.length || 0
}
</script>

<style lang="scss" scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.sidebar {
  width: 400px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  height: 100vh;

  .sidebar-header {
    flex: 0 0 auto;
    padding: 20px;
    border-bottom: 1px solid #e4e7ed;
    background: white;

    .app-title {
      display: flex;
      align-items: center;
      margin: 0 0 16px 0;
      font-size: 20px;
      font-weight: 600;
      color: #303133;

      .el-icon {
        margin-right: 8px;
        color: #409eff;
      }
    }

    .new-chat-btn {
      width: 100%;
    }
  }

  .chat-history {
    flex: 0 0 auto;
    padding: 20px;
    overflow: hidden;

    .history-section {
      margin-bottom: 16px;

      h3 {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
        margin: 0 0 6px 0;
      }

      .section-subtitle {
        font-size: 14px;
        color: #909399;
        margin: 0;
      }
    }

    .task-description {
      margin-bottom: 16px;

      h4 {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin: 0 0 8px 0;
      }

      p {
        font-size: 13px;
        color: #606266;
        line-height: 1.5;
        margin: 0 0 8px 0;
      }
    }

    .feature-tips {
      margin-top: 12px;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      border: 1px solid #e4e7ed;

      p {
        font-size: 13px;
        color: #606266;
        font-weight: 500;
        margin: 0;
      }
    }
  }

  .chat-messages {
    flex: 1;
    padding: 15px 20px;
    overflow-y: auto;
    min-height: 0;
    max-height: calc(100vh - 400px); /* 为输入区域预留更多空间 */

    .message {
      margin-bottom: 16px;

      &.user {
        .user-message {
          display: flex;
          flex-direction: column;
          align-items: flex-end;

          .message-content {
            background: #409eff;
            color: white;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
            max-width: 80%;
            word-wrap: break-word;
            font-size: 14px;
            line-height: 1.4;
          }

          .message-time {
            font-size: 12px;
            color: #909399;
            margin-top: 4px;
          }
        }
      }

      &.chat_response {
        .bot-message {
          display: flex;
          align-items: flex-start;

          .bot-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            flex-shrink: 0;

            .el-icon {
              color: #606266;
            }
          }

          .message-content {
            flex: 1;

            .message-text {
              background: white;
              padding: 12px 16px;
              border-radius: 4px 18px 18px 18px;
              border: 1px solid #e4e7ed;
              font-size: 14px;
              line-height: 1.6;
              color: #303133;
            }

            .message-time {
              font-size: 12px;
              color: #909399;
              margin-top: 4px;
            }
          }
        }
      }
    }

    .typing-indicator {
      display: flex;
      align-items: flex-start;

      .bot-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        flex-shrink: 0;

        .el-icon {
          color: #606266;
        }
      }

      .typing-dots {
        background: white;
        padding: 12px 16px;
        border-radius: 4px 18px 18px 18px;
        border: 1px solid #e4e7ed;
        display: flex;
        align-items: center;

        span {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #c0c4cc;
          margin: 0 2px;
          animation: typing 1.4s infinite ease-in-out;

          &:nth-child(1) { animation-delay: -0.32s; }
          &:nth-child(2) { animation-delay: -0.16s; }
        }
      }
    }
  }

  .chat-input {
    flex: 0 0 auto;
    padding: 20px;
    border-top: 1px solid #e4e7ed;
    background: white;
    min-height: 160px; /* 确保有足够的高度显示按钮 */

    .input-container {
      .uploaded-file-card {
        margin-bottom: 12px;
        background: #ffffff;
        border: 1px solid #e4e7ed;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        overflow: hidden;
        
        &:hover {
          border-color: #409eff;
          box-shadow: 0 4px 16px rgba(64, 158, 255, 0.15);
        }
        
        .file-card-header {
          display: flex;
          align-items: center;
          padding: 12px 16px 8px 16px;
          
          .file-icon {
            flex-shrink: 0;
            margin-right: 8px;
            color: #409eff;
            font-size: 16px;
          }
          
          .file-name {
            flex: 1;
            font-size: 14px;
            font-weight: 500;
            color: #303133;
            word-break: break-all;
            overflow-wrap: break-word;
            line-height: 1.4;
          }
          
          .close-btn {
            flex-shrink: 0;
            padding: 4px;
            color: #909399;
            
            &:hover {
              color: #f56c6c;
            }
            
            :deep(.el-icon) {
              font-size: 14px;
            }
          }
        }
        
        .file-card-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 16px 12px 16px;
          background: #f8f9fa;
          border-top: 1px solid #f0f0f0;
          
          .file-size {
            font-size: 12px;
            color: #909399;
          }
          
          .analyze-btn {
            border-radius: 4px;
            font-size: 12px;
            padding: 4px 12px;
            height: 28px;
            
            :deep(.el-icon) {
              font-size: 12px;
            }
          }
        }

      }
      
      .input-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;
        padding: 8px 0; /* 添加内边距 */
        min-height: 40px; /* 确保按钮区域有足够高度 */
      }
    }
  }
}

.agent-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;

  .workspace-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid #e4e7ed;
    background: white;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  .workspace-tabs {
    flex: 1;
    padding: 0;
    overflow-y: auto;

    :deep(.el-tabs__header) {
      margin: 0;
      padding: 0 24px;
      background: #fafbfc;
      border-bottom: 1px solid #e4e7ed;
    }

    :deep(.el-tabs__content) {
      padding: 0;
      height: calc(100vh - 120px);
      overflow-y: hidden;
    }

    .tab-content {
      padding: 0px;
      height: calc(100vh - 180px);
      overflow-y: auto;

      .status-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;

        h4 {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
          margin: 0;
        }
      }

      .processing-steps {
        margin-bottom: 20px;

        :deep(.el-timeline-item__content) {
          .step-content {
            h5 {
              font-size: 14px;
              font-weight: 600;
              color: #303133;
              margin: 0 0 8px 0;
            }

            p {
              font-size: 13px;
              color: #606266;
              margin: 0 0 8px 0;
            }

            .step-progress {
              margin-top: 8px;
            }
          }
        }
      }

      .current-processing {
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .rotating {
            animation: rotate 2s linear infinite;
          }
        }
      }

      .analysis-result {
        height: 100%;
        display: flex;
        flex-direction: column;
        
        .result-header {
          margin-bottom: 20px;

          .result-title {
            h4 {
              font-size: 18px;
              font-weight: 600;
              color: #303133;
              margin: 0 0 8px 0;
              display: flex;
              align-items: center;
              
              // 文件图标样式
              &:first-child {
                margin-right: 8px;
              }
            }
          }

          .result-meta {
            display: flex;
            align-items: center;
            gap: 12px;

            .result-time {
              font-size: 13px;
              color: #909399;
            }
          }
        }

        .result-content {
          .info-card {
            margin-bottom: 16px;

            :deep(.el-card__header) {
              padding: 12px 16px;
              background: #fafbfc;

              h5 {
                font-size: 14px;
                font-weight: 600;
                color: #303133;
                margin: 0;
              }
            }

            :deep(.el-card__body) {
              padding: 16px;
            }

            .analysis-content {
              font-size: 14px;
              line-height: 1.6;
              color: #303133;

              h4 {
                font-size: 16px;
                font-weight: 600;
                color: #303133;
                margin: 16px 0 8px 0;
              }

              ul {
                margin: 8px 0;
                padding-left: 20px;
              }

              li {
                margin: 4px 0;
              }
            }

            .suggestions-content {
              ul {
                margin: 0;
                padding-left: 20px;

                li {
                  font-size: 14px;
                  color: #606266;
                  line-height: 1.6;
                  margin: 8px 0;
                }
              }
            }
          }
        }
      }

      .document-preview {
        .preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 12px;
          border-bottom: 1px solid #e4e7ed;

          h4 {
            font-size: 16px;
            font-weight: 600;
            color: #303133;
            margin: 0;
          }

          .file-info {
            display: flex;
            align-items: center;
            gap: 8px;

            .file-size {
              font-size: 12px;
              color: #909399;
            }
          }
        }

        .preview-content {
          .text-preview {
            .file-content {
              background: #f8f9fa;
              border: 1px solid #e4e7ed;
              border-radius: 6px;
              padding: 16px;
              margin-bottom: 20px;

              pre {
                margin: 0;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.5;
                color: #303133;
                white-space: pre-wrap;
                word-wrap: break-word;
              }
            }

            .loading-content {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              padding: 40px;
              color: #909399;

              .el-icon {
                font-size: 24px;
                margin-bottom: 12px;
              }

              p {
                margin: 0;
                font-size: 14px;
              }
            }
          }

          .binary-preview {
            .file-info-display {
              margin-bottom: 20px;

              .document-icon {
                display: flex;
                flex-direction: column;
                align-items: center;
                margin-bottom: 16px;

                .el-icon {
                  margin-bottom: 8px;
                }

                .icon-text {
                  font-size: 14px;
                  font-weight: 600;
                  color: #303133;
                  margin: 0;
                }
              }

              .preview-notice {
                margin-top: 16px;

                :deep(.el-alert__content) {
                  .notice-content {
                    p {
                      margin: 8px 0;
                      font-size: 13px;
                      line-height: 1.5;

                      strong {
                        color: #303133;
                        font-weight: 600;
                      }
                    }

                    ul {
                      margin: 8px 0;
                      padding-left: 20px;

                      li {
                        margin: 4px 0;
                        font-size: 13px;
                        line-height: 1.4;
                        color: #67c23a;
                      }
                    }
                  }
                }
              }
            }
          }

          .preview-actions {
            display: flex;
            justify-content: center;
            gap: 12px;
            padding-top: 20px;
            border-top: 1px solid #e4e7ed;
          }
        }
      }

      .empty-state {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 400px;
      }

      .export-options {
        .export-card {
          margin-bottom: 20px;

          :deep(.el-card__header) {
            padding: 16px 20px;
            background: #fafbfc;

            .card-header {
              display: flex;
              align-items: center;
              font-size: 16px;
              font-weight: 600;
              color: #303133;

              .el-icon {
                margin-right: 8px;
                color: #409eff;
              }
            }
          }

          :deep(.el-card__body) {
            padding: 20px;

            p {
              font-size: 14px;
              color: #606266;
              line-height: 1.6;
              margin: 0 0 16px 0;
            }

            .export-actions {
              display: flex;
              justify-content: flex-end;
              gap: 8px;
            }

            .custom-export {
              :deep(.el-checkbox-group) {
                display: flex;
                flex-direction: column;
                gap: 8px;
              }
            }
          }
        }
      }
    }
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: 50vh;
    
    .chat-input {
      .input-container {
        .uploaded-file-info {
          flex-direction: column;
          align-items: stretch;
          
          .file-info-container {
            max-width: 100%;
            margin-bottom: 8px;
            
            .file-details {
              .file-name {
                font-size: 13px;
              }
            }
          }
          
          .analyze-btn {
            width: 100%;
            align-self: stretch;
          }
        }
      }
    }
  }
  
  .agent-workspace {
    height: 50vh;
  }
  
  // 移动端悬浮按钮优化
  .result-actions-float {
    padding: 12px 16px;
    gap: 8px;
    
    .el-button {
      flex: 1;
      max-width: none;
      height: 32px;
      font-size: 12px;
      
      .el-icon {
        font-size: 14px;
      }
    }
  }
}

// 结果容器样式
.results-container {
  position: relative;
  height: calc(100vh - 400px);
  display: flex;
  flex-direction: column;
}

// 悬浮操作按钮样式
.result-actions-float {
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-top: 1px solid #e4e7ed;
  border-radius: 12px 12px 0 0;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.98);
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
  }
  
  .el-button {
    flex: 1;
    max-width: 120px;
    height: 36px;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    &.el-button--primary {
      background: linear-gradient(135deg, #409eff, #1890ff);
      border: none;
      
      &:hover {
        background: linear-gradient(135deg, #1890ff, #096dd9);
      }
    }
  }
}

// 内容分析结果样式
.content-analysis-result {
  .analysis-section {
    margin-bottom: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #e4e7ed;
    }
    
    .summary-text {
      font-size: 14px;
      line-height: 1.6;
      color: #606266;
      margin: 0;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      border-left: 4px solid #409eff;
    }
    
    .keywords {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      
      .keyword-tag {
        margin: 0;
      }
    }
  }
}

// 文档结构摘要样式
.document-summary {
  .summary-section {
    margin-bottom: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #e4e7ed;
    }
    
    .abstract-text {
      font-size: 14px;
      line-height: 1.6;
      color: #606266;
      margin: 0;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      border-left: 4px solid #52c41a;
    }
  }
  
  .function-list, .api-list {
    margin-bottom: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #e4e7ed;
    }
  }
}

// 关键词分析样式
.keyword-analysis {
  .keywords-section {
    margin-bottom: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #e4e7ed;
    }
  }
  
  .primary-keywords {
    margin-bottom: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #e4e7ed;
    }
    
    :deep(.el-table) {
      border-radius: 6px;
      overflow: hidden;
      
      .el-table__header {
        background: #f8f9fa;
        
        th {
          background: #f8f9fa;
          color: #303133;
          font-weight: 600;
        }
      }
      
      .el-table__body {
        tr:hover {
          background: #f0f9ff;
        }
      }
    }
  }
  
  .semantic-clusters {
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #e4e7ed;
    }
    
    .cluster-item {
      margin-bottom: 12px;
      padding: 12px;
      background: #f8f9fa;
      border-radius: 6px;
      border-left: 4px solid #faad14;
      
      .cluster-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .cluster-name {
          font-size: 14px;
          font-weight: 600;
          color: #303133;
        }
      }
      
      .cluster-keywords {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }
    }
  }
}

// AI分析结果样式
.ai-analysis-result {
  .ai-analysis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    h5 {
      margin: 0;
    }
  }
  
  .ai-response-content {
    margin-top: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 12px 0;
      padding-bottom: 4px;
      border-bottom: 1px solid #e4e7ed;
    }
    
    .ai-response-text {
      background: #f8f9fa;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      padding: 16px;
      
      :deep(h6) {
        color: #409eff;
        font-weight: 600;
        margin: 16px 0 8px 0;
        
        &:first-child {
          margin-top: 0;
        }
      }
      
      :deep(strong) {
        color: #303133;
        font-weight: 600;
      }
      
      :deep(em) {
        color: #606266;
        font-style: italic;
      }
      
      :deep(code) {
        background: #e6f7ff;
        color: #1890ff;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
      }
      
      :deep(li) {
        margin: 4px 0;
        color: #606266;
        line-height: 1.5;
      }
    }
  }
  
  .custom-prompt-section {
    margin-top: 16px;
    
    h6 {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }
    
    .custom-prompt-text {
      font-size: 13px;
      color: #909399;
      background: #f5f7fa;
      padding: 8px 12px;
      border-radius: 4px;
      margin: 0;
      font-style: italic;
    }
  }
}

// Markdown样式
.markdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

// 分析总结样式
.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  h5 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: #303133;
  }
}

.summary-content {
  .summary-text {
    font-size: 14px;
    line-height: 1.8;
    color: #606266;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 6px;
    border-left: 4px solid #67c23a;
    margin: 0;
    
    :deep(br) {
      margin-bottom: 8px;
    }
    
    :deep(strong) {
      color: #303133;
      font-weight: 600;
    }
    
    :deep(em) {
      color: #909399;
      font-style: italic;
    }
  }
}

.markdown-content {
  .markdown-preview {
    padding: 16px;
    background: #fafafa;
    border-radius: 6px;
    
    :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
      color: #303133;
      margin: 16px 0 8px 0;
      padding-bottom: 8px;
      border-bottom: 1px solid #e4e7ed;
      font-weight: 600;
    }
    
    :deep(h1) { font-size: 28px; }
    :deep(h2) { font-size: 24px; }
    :deep(h3) { font-size: 20px; }
    :deep(h4) { font-size: 18px; }
    :deep(h5) { font-size: 16px; }
    :deep(h6) { font-size: 14px; }
    
    :deep(p) {
      margin: 8px 0;
      line-height: 1.6;
      color: #606266;
    }
    
    :deep(ul), :deep(ol) {
      margin: 8px 0;
      padding-left: 24px;
      
      li {
        margin: 4px 0;
        line-height: 1.5;
        color: #606266;
      }
    }
    
    :deep(blockquote) {
      margin: 16px 0;
      padding: 8px 16px;
      background: #f4f4f5;
      border-left: 4px solid #409eff;
      color: #606266;
      font-style: italic;
    }
    
    :deep(code) {
      padding: 2px 4px;
      background: #f1f2f3;
      border-radius: 3px;
      font-family: 'Courier New', monospace;
      font-size: 12px;
      color: #e6a23c;
    }
    
    :deep(pre) {
      margin: 16px 0;
      padding: 16px;
      background: #2d3748;
      color: #e2e8f0;
      border-radius: 6px;
      overflow-x: auto;
      
      code {
        background: none;
        color: inherit;
        padding: 0;
      }
    }
    
    :deep(table) {
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      
      th, td {
        padding: 8px 12px;
        border: 1px solid #e4e7ed;
        text-align: left;
      }
      
      th {
        background: #f5f7fa;
        font-weight: 600;
        color: #303133;
      }
      
      td {
        color: #606266;
      }
    }
    
    :deep(hr) {
      margin: 24px 0;
      border: none;
      border-top: 2px solid #e4e7ed;
    }
    
    :deep(strong) {
      font-weight: 600;
      color: #303133;
    }
    
    :deep(em) {
      font-style: italic;
      color: #909399;
    }
    
    :deep(a) {
      color: #409eff;
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
}

.no-content {
  color: #909399;
  font-style: italic;
  text-align: center;
  padding: 20px;
}

// 结果容器样式优化
        .results-container {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

// 自适应滚动条样式优化
.analysis-scrollbar {
  flex: 1;
  height: calc(100vh - 400px);
  
  :deep(.el-scrollbar__wrap) {
    overflow-x: hidden;
  }
  
  :deep(.el-scrollbar__view) {
    padding: 0;
  }
}

.ai-content-scrollbar,
.markdown-content-scrollbar,
.document-content-scrollbar {
  :deep(.el-scrollbar__wrap) {
    overflow-x: hidden;
  }
  
  :deep(.el-scrollbar__view) {
    padding: 8px 0;
  }
  
  :deep(.el-scrollbar__bar) {
    .el-scrollbar__thumb {
      background-color: rgba(144, 147, 153, 0.5);
      border-radius: 4px;
      
      &:hover {
        background-color: rgba(144, 147, 153, 0.8);
      }
    }
  }
}

// 不同滚动区域的特殊优化
.ai-content-scrollbar {
  // AI内容区域的特殊样式
  :deep(.el-scrollbar__view) {
    min-height: 200px;
  }
}

.markdown-content-scrollbar {
  // Markdown内容区域的特殊样式
  :deep(.el-scrollbar__view) {
    min-height: 300px;
  }
}

.document-content-scrollbar {
  // 文档内容区域的特殊样式
  :deep(.el-scrollbar__view) {
    min-height: 150px;
  }
  
  .content-text {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #303133;
    white-space: pre-wrap;
    word-wrap: break-word;
    margin: 0;
  }
}

// 响应式适配
@media (max-width: 1200px) {
  .analysis-scrollbar {
    height: calc(100vh - 420px) !important;
  }
  
  .ai-content-scrollbar {
    max-height: 55vh !important;
  }
  
  .markdown-content-scrollbar {
    max-height: 65vh !important;
  }
  
  .document-content-scrollbar {
    max-height: 45vh !important;
  }
}

@media (max-width: 768px) {
  .analysis-scrollbar {
    height: calc(100vh - 440px) !important;
  }
  
  .ai-content-scrollbar {
    max-height: 50vh !important;
  }
  
  .markdown-content-scrollbar {
    max-height: 60vh !important;
  }
  
  .document-content-scrollbar {
    max-height: 40vh !important;
  }
}
</style> 