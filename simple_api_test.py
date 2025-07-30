import requests
import json
import os
import glob
import shutil
from datetime import datetime
from pathlib import Path
import subprocess
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalProjectAnalyzer:
    """本地项目分析器"""
    
    def __init__(self, local_server_url="http://localhost:30000/ls/", git_base_path="/Users/renyu/Documents/create_project"):
        self.local_server_url = local_server_url.rstrip('/')
        self.git_base_path = Path(git_base_path)
        self.git_base_path.mkdir(parents=True, exist_ok=True)
        
    def list_local_projects(self):
        """列出本地项目"""
        projects = []
        
        # 1. 检查/Users/renyu/Documents/create_project
        if self.git_base_path.exists():
            for item in self.git_base_path.iterdir():
                if item.is_dir() and self._is_project_directory(item):
                    projects.append({
                        "name": item.name,
                        "path": str(item),
                        "source": "gitlab"
                    })
        
      
        
        return projects
    
    def _is_project_directory(self, path):
        """判断是否为项目目录"""
        path = Path(path)
        indicators = [
            "pom.xml",
            "build.gradle", 
            "package.json",
            "requirements.txt",
            "src",
            ".git"
        ]
        
        for indicator in indicators:
            if (path / indicator).exists():
                return True
        return False
    
    def analyze_project_structure(self, project_path):
        """分析项目结构"""
        logger.info(f"分析项目结构: {project_path}")
        
        analysis = {
            "project_name": os.path.basename(project_path),
            "project_path": project_path,
            "technology_stack": [],
            "services": [],
            "source_files": [],
            "config_files": [],
            "git_info": {}
        }
        
        project_path = Path(project_path)
        
        # 检测技术栈
        if (project_path / "pom.xml").exists():
            analysis["technology_stack"].append("Java Maven")
            
        if (project_path / "build.gradle").exists():
            analysis["technology_stack"].append("Java Gradle")
            
        if (project_path / "package.json").exists():
            analysis["technology_stack"].append("Node.js")
            
        if (project_path / "requirements.txt").exists():
            analysis["technology_stack"].append("Python")
            
        # 查找源代码文件
        source_patterns = [
            "**/*.java",
            "**/*.js", 
            "**/*.py",
            "**/*.ts"
        ]
        
        for pattern in source_patterns:
            files = list(project_path.glob(pattern))
            analysis["source_files"].extend([str(f) for f in files[:10]])  # 限制数量
            
        # 查找配置文件
        config_patterns = [
            "application.yml",
            "application.yaml",
            "application.properties",
            "config.yml",
            "pom.xml",
            "package.json"
        ]
        
        for pattern in config_patterns:
            config_file = project_path / pattern
            if config_file.exists():
                analysis["config_files"].append(str(config_file))
        
        # Git信息
        if (project_path / ".git").exists():
            analysis["git_info"] = self._get_git_info(project_path)
            
        return analysis
    
    def _get_git_info(self, project_path):
        """获取Git信息"""
        git_info = {}
        try:
            # 获取当前分支
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                git_info["current_branch"] = result.stdout.strip()
            
            # 获取远程仓库地址
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                git_info["remote_url"] = result.stdout.strip()
                
        except Exception as e:
            logger.warning(f"获取Git信息失败: {e}")
            
        return git_info

def test_enhanced_langgraph_api():
    """增强版LangGraph API测试 - 支持本地项目读取和分析"""
    print("🚀 增强版LangGraph编码智能体API集成测试")
    print("=" * 70)
    
    # 创建项目分析器
    analyzer = LocalProjectAnalyzer()
    
    # 1. 扫描本地项目
    print("🔍 扫描本地项目...")
    projects = analyzer.list_local_projects()
    print(f"发现 {len(projects)} 个项目:")
    for i, project in enumerate(projects, 1):
        print(f"  {i}. {project['name']} ({project['source']}) - {project['path']}")
    
    # 2. 选择或创建项目
    selected_project = None
    existing_project_analysis = None
    
    if projects:
        # 选择第一个项目进行分析
        selected_project = projects[0]
        print(f"\n📋 选择项目: {selected_project['name']}")
        
        # 分析现有项目
        existing_project_analysis = analyzer.analyze_project_structure(selected_project['path'])
        print(f"✅ 项目分析完成!")
        print(f"  - 技术栈: {', '.join(existing_project_analysis['technology_stack'])}")
        print(f"  - 源文件数: {len(existing_project_analysis['source_files'])}")
        print(f"  - 配置文件数: {len(existing_project_analysis['config_files'])}")
        print(f"  - Git分支: {existing_project_analysis['git_info'].get('current_branch', 'N/A')}")
    
    # 3. 设计文档内容
    document_content = """
设计文档 - 一局对接链数优化V0.1
1. 系统架构设计
1.1 项目介绍
一局对接链数的项目上线后，核心企业反馈，希望就已推送至平台的数据，在核心企业内部系统内修改部分信息（如额度信息）后，使用原业务编号再次推送至平台。就目前的接口校验逻辑，相同业务编号的业务数据不可重复推送。因而，需要结合核心企业需求，对接口的校验逻辑进行调整。
建设目标及路线。调整接口校验逻辑，兼容核心企业重推数据的场景。
1.2 功能需求说明
1.2.1 链数额度功能调整
调整说明:本期，对原"链数额度"功能做如下调整：
- 功能名称由"链数额度"变更为"额度管理"；
- 页面右上方新增"组织单元额度"按钮，当且仅当当前登录企业为多组织企业时展示该按钮。用户点击"组织单元额度"按钮，则跳转至"组织单元额度"列表页。
- 列表新增字段"额度类型"，置于"额度名称"之后，若为链数额度则取值为"链数额度"。
1.2.2 新增组织单元额度功能
调整说明:本期在核心企业侧链数额度功能下，新增"组织单元额度"列表页。支持用户查询当前登录企业下的具体组织单元的链数额度、云信额度明细。
a.筛选字段：
序号	字段名	类型格式	长度	默认值	必填	规则
1	组织单元名称	文本输入框	-	-	-	模糊搜索
2	额度名称	文本输入框	-	-	-	模糊搜索
3	额度类型	下拉列表	-	链数额度	-	下拉选项：链数额度、云信额度、全部
b.汇总字段：
序号	字段名	类型格式	规则
1	总额度（元）	数值	满足筛选条件的列表数据的“已分配额度（元）”之和
2	已用额度（元）	数值	满足筛选条件的列表数据的“已用额度（元）”之和
3	可用额度（元）	数值	满足筛选条件的列表数据的“可用额度（元）”之和
备注：筛选条件更新后，汇总值需要同步更新计算。
c.列表字段：
序号	字段名	类型格式	规则
1	组织单元名称	字符串	无
2	额度名称	字符串	无
3	额度类型	字符串	无
4	已分配额度（元）	数值	无
5	已用额度（元）	数值	无
6	可用额度（元）	数值	无
备注：列表默认按照组织单元名称为主要关键字、额度类型为次要关键字降序排列。

1.3 总体架构
采用微服务架构模式，实现松耦合、高可扩展的系统设计：
- 涉及2个后端服务：
1. 用户服务：zqyl-user-center-service
2. 确权开立服务：crcl-open

- 涉及2个数据库：
1. 用户数据库：MySQL 
2. 缓存：Redis

1.4 技术栈选型
- 后端框架：Spring Boot 2.7.x + Spring Cloud 2021.x
- 数据访问：MyBatis Plus 3.5.x
- 数据库：MySQL 8.0
- 缓存：Redis 6.0
- 消息队列：RabbitMQ 3.8
- 服务发现：Nacos
- 配置中心：Nacos
- 后端分页：pageHelper
- 部署：将代码提交到git分支即可

2. 服务设计

2.1 用户服务 (zqyl-user-center-service)
职责：用户管理、权限控制、角色管理

2.1.1 核心模块：
- 组织单元管理

2.1.2 API设计：
2.1.2.1 新增接口：
uri : GET /general/multiorgManage/queryCompanyUnitList    
method: GET
description:查询企业组织单元列表
入参示例：
{
  "unitCode": "sdf1",  #组织单元编号
  "openStatus": 1 ,    #组织单元状态 1：正常；0：禁用 默认全部
  "unitList" :[1,2,234]  #组织单元id 必传 
}

返参示例：
{
  "data": [
    {
      "unitId" : 234234 ,     #组织单元id 必传 
      "unitTypeDicType" : 1 , #组织单元类型 1：开立，2：支付
      "unitTypeId" : 12   ,   #组织单元类型表id 
      "openStatus" : 1   ,    #组织单元状态  1：正常；0：禁用 默认全部
      "unitCode" : "sdfsdfsd",#组织编号
      "unitName" : "测试单元" #组织单元名称
    }
  ]
}

2.1.3 数据库表设计：
CREATE TABLE t_cust_multiorg_unit(
  id bigint(20) NOT NULL COMMENT '主键id',
  company_id bigint(20) NOT NULL COMMENT '企业id',
  mutilorg_id bigint(10) NOT NULL COMMENT '多组织id',
  unit_code varchar(50) NOT NULL COMMENT '组织单元编号',
  unit_name varchar(255) NOT NULL COMMENT '组织单元名称',
  remark varchar(500) DEFAULT NULL COMMENT '备注',
  platform_type tinyint(2) NOT NULL COMMENT '平台类型(1云信2云租3云保)',
  status tinyint(2) NOT NULL COMMENT '状态1正常0删除',
  create_id bigint(20) NOT NULL COMMENT '创建人id',
  oper_user_name varchar(255) DEFAULT NULL COMMENT '创建人用户名',
  create_time datetime NOT NULL COMMENT '创建时间',
  modify_id bigint(20) DEFAULT NULL COMMENT '修改人id',
  modify_user_name varchar(255) DEFAULT NULL COMMENT '最后修改用户名',
  modify_time datetime DEFAULT NULL COMMENT '修改时间',
  PRIMARY KEY(id),
  KEY pk_company_id(company_id) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='多组织单元表';

2.2.4 本次项目依赖服务：
依赖服务名称：无

2.2 确权开立服务 (crcl-open)
职责：确权开立、额度管理

2.2.1 核心模块：
- 确权开立模块
- 额度管理模块

2.2.2 API设计：
2.2.2.1 新增接口：
uri :  /crcl-open-api/lsLimit/listUnitLimitByCompanyId    
method: GET
description:组织单元额度列表

入参示例：
{
  "gwCompanyId" : 1,   #当前登录企业id  ,必传
  "unitName" : "abs",  #组织单元名称（模糊搜索）
  "limitSource" : "",  #额度名称（模糊搜索）
  "bizType" : 1,       #10：云信额度，80：链数额度（默认）
  "page" : 1,          #页码，必传
  "pageRow" : 10       #每页记录数，必传 
}

返参示例：
{
  "totalLimitAmt": 100 ,       #总额度
  "usedLimitAmt" :1 ,          #已用额度
  "usableLimitAmt" : 10,       #可用额度
  "unitLimitListDetail" : [{   #额度信息
    "unitName":"sdfs",         #组织单元名称
    "limitSource" : "232f",    #额度名称
    "bizType":1,               #额度类型：10：云信额度 80：链数额度
    "usedLimitAmt" : 1,        #已分配额度
    "usableLimitAmt" : 1,      #已用额度
    "totalLimitAmt" :1         #可用额度
  }]
}

特殊要求：
1、采用pagehelper进行分页
2、需要调用zqyl-user-center-service服务的/queryCompanyUnitList接口获取组织单元详细信息

2.2.2.2 新增接口：
uri : /crcl-open-api/lsLimit/listUnitLimitByCompanyIdExport   
method: GET
description: 组织单元额度列表导出


入参示例：
{
  "gwCompanyId" : 1,   #当前登录企业id  ,必传
  "unitName" : "abs",  #组织单元名称（模糊搜索）
  "limitSource" : "",  #额度名称（模糊搜索）
  "bizType" : 1,       #10：云信额度，80：链数额度（默认）
  "page" : 1,          #页码，必传
  "pageRow" : 10       #每页记录数，必传 
}

返参示例：
{
  "flag" : 1,    #0文件生成失败，1文件生成成功
  "msg": "",     #flag=0 提示内容
  "data" :" "    #flag=1 文件下载地址 
}

特殊要求：
1、文件生成在本地目录，采用本地链接形式返回路径。
2、文件类型为Excel列表，文件类型：xlsx
3、列表头列内容：组织单元名称、额度名称、额度类型、已分配额度（元）、已用额度（元）、可用额度（元）
4、需要调用zqyl-user-center-service服务的/queryCompanyUnitList接口获取组织单元详细信息

2.2.3 数据库表设计：无

2.2.4 本次项目依赖服务：
依赖服务名称：zqyl-user-center-service


3 执行要求
3.1 涉及服务范围
本次没有新增服务，服务范围为：
1. 用户服务：zqyl-user-center-service，git地址：http://localhost:30000/ls/zqyl-user-center-service.git
2. 确权开立服务：crcl-open，git地址：http://localhost:30000/ls/crcl-open.git

3.2 涉及数据库范围
本次没有新增数据库，数据库范围为：
3.2.1 用户数据库：MySQL 
数据库配置
  url: jdbc:mysql://localhost:6446/dbwebappdb?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&characterEncoding=utf8&useUnicode=true
    username: dbwebapp
    password: dbwebapp
    driver-class-name: com.mysql.cj.jdbc.Driver


3.2.2 缓存：
redis:
  host: localhost
  port: 6379
  db: 0
  password: ''

3.3 涉及接口范围
本次新增接口，已经按服务范围进行划分，详见设计文档2服务设计部分。

""" + (json.dumps(existing_project_analysis, indent=2, ensure_ascii=False) if existing_project_analysis else "无现有项目分析")

    # 4. 增强的API调用
    api_url = "http://localhost:8082/api/coder-agent/process-document"
    project_name = f"链数中建一局_{int(datetime.now().timestamp())}"
    
    request_data = {
        "document_content": document_content,
        "project_name": project_name,
        "use_langgraph": True,
        "output_path": str(analyzer.git_base_path),
        "existing_project_path": selected_project['path'] if selected_project else None,
        "target_branch": "feature/optimization",
        "project_task_id": "1231000002"
    }
    
    print(f"\n🚀 调用增强版API: {api_url}")
    print(f"📋 项目名称: {project_name}")
    print(f"🔧 使用LangGraph: True")
    print(f"📄 文档长度: {len(document_content)} 字符")
    print(f"📁 输出路径: {analyzer.git_base_path}")
    print(f"🌿 目标分支: feature/optimization")
    print(f"🔗 现有项目: {selected_project['name'] if selected_project else '无'}")
    print("-" * 70)
    
    try:
        response = requests.post(api_url, json=request_data, timeout=5000)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            
            # 显示基本结果
            print(f"📊 响应状态: {result.get('status', 'unknown')}")
            print(f"🔄 工作流类型: {result.get('workflow_type', 'unknown')}")
            print(f"⏰ 响应时间: {result.get('timestamp', 'unknown')}")
            
            # 显示工作流结果
            if "workflow_result" in result:
                workflow_result = result["workflow_result"]
                print(f"🎯 工作流状态: {workflow_result.get('status', 'unknown')}")
                
                if workflow_result.get('status') == 'failed':
                    print(f"❌ 工作流错误: {workflow_result.get('error', 'unknown')}")
                else:
                    print(f"✅ 工作流执行成功!")
                    
                    # 显示生成的文件
                    if workflow_result.get('output_path'):
                        print(f"📁 代码生成路径: {workflow_result['output_path']}")
                        
                        # 检查生成的文件
                        output_path = Path(workflow_result['output_path'])
                        if output_path.exists():
                            print(f"📋 生成的项目文件:")
                            for item in output_path.iterdir():
                                if item.is_dir():
                                    print(f"  📁 {item.name}/")
                                else:
                                    print(f"  📄 {item.name}")
            
            # 保存结果
            result_file = f"enhanced_langgraph_result_{int(datetime.now().timestamp())}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"📁 结果已保存到: {result_file}")
            
            print("")
            print("🎉 增强版测试完成! LangGraph工作流执行成功")
            return True
            
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("💡 请确保API服务器已启动 (python src/apis/api_server.py)")
        return False
    except requests.exceptions.Timeout:
        print("❌ API调用超时 (5分钟)")
        return False
    except Exception as e:
        print(f"❌ API调用异常: {e}")
        return False

# 保留原有的简单测试函数
def test_langgraph_api():
    print("LangGraph编码智能体API集成测试")
    print("=" * 60)
    
    # 测试文档内容
    document_content = """
需求文档 - 一局对接链数优化V0.1

项目背景：
本项目旨在优化一局与链数系统的对接，提升数据传输效率和系统稳定性。

功能需求：
1. 用户管理系统 - 用户注册、登录、权限管理
2. 数据同步服务 - 实时数据同步、验证、监控
3. API网关 - 统一接口管理、路由、负载均衡
4. 监控告警系统 - 性能监控、异常告警、日志管理

技术要求：Spring Boot + MyBatis + MySQL + Redis + 微服务架构
"""
    
    # API调用
    api_url = "http://localhost:8082/api/coder-agent/process-document"
    project_name = f"一局对接链数优化_{int(datetime.now().timestamp())}"
    
    request_data = {
        "document_content": document_content,
        "project_name": project_name,
        "use_langgraph": True,
        "project_task_id": "1231000002"
    }
    
    print(f"🚀 调用API: {api_url}")
    print(f"📋 项目名称: {project_name}")
    print(f"🔧 使用LangGraph: True")
    print(f"📄 post参数: {request_data}")
    print("-" * 60)
    
    try:
        response = requests.post(api_url, json=request_data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            
            # 显示基本结果
            print(f"📊 响应状态: {result.get('status', 'unknown')}")
            print(f"🔄 工作流类型: {result.get('workflow_type', 'unknown')}")
            print(f"⏰ 响应时间: {result.get('timestamp', 'unknown')}")
            
            # 保存结果
            result_file = f"langgraph_test_result_{int(datetime.now().timestamp())}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"📁 结果已保存到: {result_file}")
            
            # 显示部分结果
            if "data" in result:
                data = result["data"]
                print("")
                print("📋 工作流执行结果:")
                print(f"  - 项目名称: {data.get('project_name', 'unknown')}")
                print(f"  - 执行ID: {data.get('execution_id', 'unknown')}")
                print(f"  - 状态: {data.get('status', 'unknown')}")
            
            print("")
            print("🎉 测试完成! LangGraph工作流执行成功")
            return True
            
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("💡 请确保API服务器已启动")
        return False
    except requests.exceptions.Timeout:
        print("❌ API调用超时 (5分钟)")
        return False
    except Exception as e:
        print(f"❌ API调用异常: {e}")
        return False

if __name__ == "__main__":
    print("选择测试模式:")
    print("1. 增强版测试 (支持本地项目分析)")
    
    test_enhanced_langgraph_api()
 