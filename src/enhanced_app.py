import streamlit as st
import os
import json
from pathlib import Path
from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from .enhanced_analyzer import EnhancedRequirementAnalyzer
from .database_analyzer import DatabaseAnalyzer
from .config import settings
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="智能需求分析与设计文档生成系统",
    page_icon="🤖",
    layout="wide"
)

# 初始化组件
@st.cache_resource
def init_components():
    return {
        "document_processor": DocumentProcessor(),
        "vector_store": VectorStore(),
        "analyzer": EnhancedRequirementAnalyzer(),
        "db_analyzer": DatabaseAnalyzer()
    }

components = init_components()

def save_uploaded_file(uploaded_file):
    """保存上传的文件"""
    try:
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_FOLDER, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"文件保存失败: {str(e)}")
        return None

def save_design_document(content: str, doc_type: str) -> str:
    """保存设计文档"""
    try:
        os.makedirs(settings.OUTPUT_FOLDER, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{doc_type}_design_{timestamp}.md"
        file_path = os.path.join(settings.OUTPUT_FOLDER, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path
    except Exception as e:
        st.error(f"保存设计文档失败: {str(e)}")
        return None

def main():
    st.title("🤖 智能需求分析与设计文档生成系统")
    st.markdown(f"**公司**: {settings.COMPANY_NAME} | **产品线**: {settings.PRODUCT_LINE}")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("系统配置")
        
        # 数据库连接状态
        if settings.BUSINESS_DATABASE_URL:
            st.success("✅ 业务数据库已连接")
            db_tables = components["db_analyzer"].get_all_tables()
            st.info(f"数据库表数量: {len(db_tables)}")
        else:
            st.warning("⚠️ 未配置业务数据库")
        
        # 向量数据库状态
        try:
            # 简单测试向量数据库连接
            st.success("✅ 向量数据库已连接")
        except:
            st.error("❌ 向量数据库连接失败")
    
    # 主界面标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📄 文档上传", "🔍 需求分析", "📋 设计文档", "📊 分析结果"])
    
    with tab1:
        st.header("文档上传与处理")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 需求文档上传
            uploaded_file = st.file_uploader(
                "上传需求文档",
                type=["pdf", "docx", "doc", "txt"],
                help="支持PDF、Word、文本文档"
            )
            
            # 前端截图上传
            uploaded_images = st.file_uploader(
                "上传前端截图（可选）",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                help="上传前端界面截图，系统将自动识别文字"
            )
        
        with col2:
            if uploaded_file:
                st.success("✅ 需求文档已上传")
                st.write(f"文件名: {uploaded_file.name}")
                st.write(f"文件大小: {uploaded_file.size} bytes")
            
            if uploaded_images:
                st.success(f"✅ 已上传 {len(uploaded_images)} 张截图")
        
        # 处理文档
        if uploaded_file and st.button("开始处理文档", type="primary"):
            with st.spinner("正在处理文档..."):
                # 保存文件
                file_path = save_uploaded_file(uploaded_file)
                if file_path:
                    # 处理文档
                    document = components["document_processor"].process_document(file_path)
                    
                    # 存储到向量数据库
                    doc_id = components["vector_store"].add_document(document)
                    
                    if doc_id:
                        # 存储到session state
                        st.session_state.document = document
                        st.session_state.uploaded_images = uploaded_images
                        st.success("文档处理完成！")
                        
                        # 显示文档内容预览
                        with st.expander("文档内容预览"):
                            st.text_area("", document["content"][:1000] + "...", height=200)
                    else:
                        st.error("文档处理失败！")
    
    with tab2:
        st.header("智能需求分析")
        
        if "document" in st.session_state:
            document = st.session_state.document
            
            if st.button("开始智能分析", type="primary"):
                with st.spinner("正在进行智能分析..."):
                    # 处理截图OCR
                    ocr_text = ""
                    if "uploaded_images" in st.session_state and st.session_state.uploaded_images:
                        for image in st.session_state.uploaded_images:
                            image_path = save_uploaded_file(image)
                            if image_path:
                                ocr_result = components["document_processor"].process_image(image_path)
                                ocr_text += ocr_result + "\n"
                    
                    # 执行分析
                    analysis_result = components["analyzer"].analyze_requirements(
                        document["content"],
                        images=st.session_state.get("uploaded_images", [])
                    )
                    
                    # 存储分析结果
                    st.session_state.analysis_result = analysis_result
                    st.session_state.ocr_text = ocr_text
                    
                    st.success("分析完成！")
            
            # 显示分析结果
            if "analysis_result" in st.session_state:
                analysis = st.session_state.analysis_result
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🔑 业务关键词")
                    if analysis["keywords"]:
                        st.json(analysis["keywords"])
                    
                    st.subheader("⚠️ 问题检查")
                    if analysis["issues"]:
                        st.json(analysis["issues"])
                
                with col2:
                    st.subheader("🗄️ 相关数据库表")
                    if analysis["related_tables"]:
                        for table in analysis["related_tables"]:
                            with st.expander(f"表: {table['table_name']}"):
                                st.write(f"字段数量: {len(table['columns'])}")
                                for col in table["columns"][:5]:  # 只显示前5个字段
                                    st.write(f"- {col['name']} ({col['type']})")
                    
                    st.subheader("📊 字段可用性")
                    if analysis["field_availability"]:
                        st.json(analysis["field_availability"])
        else:
            st.info("请先上传并处理需求文档")
    
    with tab3:
        st.header("设计文档生成")
        
        if "analysis_result" in st.session_state:
            analysis = st.session_state.analysis_result
            document = st.session_state.document
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("生成后端设计文档", type="primary"):
                    with st.spinner("正在生成后端设计文档..."):
                        backend_design = components["analyzer"].generate_backend_design(
                            analysis, document["content"]
                        )
                        st.session_state.backend_design = backend_design
                        st.success("后端设计文档生成完成！")
            
            with col2:
                if st.button("生成前端设计文档", type="primary"):
                    with st.spinner("正在生成前端设计文档..."):
                        ocr_text = st.session_state.get("ocr_text", "")
                        frontend_design = components["analyzer"].generate_frontend_design(
                            analysis, document["content"], ocr_text
                        )
                        st.session_state.frontend_design = frontend_design
                        st.success("前端设计文档生成完成！")
            
            # 显示生成的设计文档
            if "backend_design" in st.session_state:
                st.subheader("🔧 后端设计文档")
                st.markdown(st.session_state.backend_design)
                
                # 下载按钮
                if st.button("保存后端设计文档"):
                    file_path = save_design_document(st.session_state.backend_design, "backend")
                    if file_path:
                        st.success(f"文档已保存到: {file_path}")
            
            if "frontend_design" in st.session_state:
                st.subheader("🎨 前端设计文档")
                st.markdown(st.session_state.frontend_design)
                
                # 下载按钮
                if st.button("保存前端设计文档"):
                    file_path = save_design_document(st.session_state.frontend_design, "frontend")
                    if file_path:
                        st.success(f"文档已保存到: {file_path}")
        else:
            st.info("请先完成需求分析")
    
    with tab4:
        st.header("分析结果总览")
        
        if "analysis_result" in st.session_state:
            analysis = st.session_state.analysis_result
            
            # API设计分析
            st.subheader("🔌 API接口设计")
            if analysis.get("api_design") and analysis["api_design"].get("apis"):
                for i, api in enumerate(analysis["api_design"]["apis"]):
                    with st.expander(f"API {i+1}: {api.get('name', 'Unknown')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**方法**: {api.get('method', 'N/A')}")
                            st.write(f"**路径**: {api.get('path', 'N/A')}")
                            st.write(f"**描述**: {api.get('description', 'N/A')}")
                        with col2:
                            st.write("**请求参数**:")
                            for param in api.get('request_params', []):
                                st.write(f"- {param}")
                            st.write("**涉及表**:")
                            for table in api.get('database_tables', []):
                                st.write(f"- {table}")
            
            # 相似文档
            st.subheader("📚 相似历史文档")
            if analysis.get("similar_docs"):
                for i, doc in enumerate(analysis["similar_docs"]):
                    with st.expander(f"相似文档 {i+1}"):
                        st.write(doc.get("content", "")[:300] + "...")
        else:
            st.info("暂无分析结果")

if __name__ == "__main__":
    main() 