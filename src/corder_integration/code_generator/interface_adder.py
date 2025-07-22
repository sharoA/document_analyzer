"""
接口添加器
用于在现有Controller文件中添加新的接口方法
"""
import os
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class InterfaceAdder:
    """接口添加器"""
    
    def __init__(self):
        """初始化接口添加器"""
        self.class_end_pattern = re.compile(r'\n\s*}$')
        self.import_section_pattern = re.compile(r'(import\s+[^;]+;\s*\n)+')
        
    def add_interface_to_controller(self, controller_info: Dict[str, str], 
                                  interface_name: str, http_method: str,
                                  api_path: str, description: str = "") -> str:
        """
        在Controller文件中添加新接口
        
        Args:
            controller_info: Controller文件信息
            interface_name: 接口名称
            http_method: HTTP方法
            api_path: API路径
            description: 接口描述
            
        Returns:
            更新后的Controller文件内容
        """
        content = controller_info['content']
        services = controller_info['services']
        
        logger.info(f"➕ 开始在Controller中添加新接口: {interface_name}")
        
        # 生成新接口方法
        new_interface_method = self._generate_interface_method(
            interface_name, http_method, api_path, description, services
        )
        
        # 检查是否需要添加import
        updated_content = self._add_required_imports(content, http_method)
        
        # 在类的结尾前添加新方法
        updated_content = self._insert_method_before_class_end(updated_content, new_interface_method)
        
        logger.info(f"✅ 成功添加接口方法到Controller")
        return updated_content
    
    def _generate_interface_method(self, interface_name: str, http_method: str,
                                 api_path: str, description: str,
                                 services: List[Dict[str, str]]) -> str:
        """
        生成接口方法代码
        
        Args:
            interface_name: 接口名称
            http_method: HTTP方法
            api_path: API路径
            description: 接口描述
            services: 可用的Service列表
            
        Returns:
            接口方法代码
        """
        # 生成映射注解 - 🔧 修复：使用完整API路径而不是接口名
        mapping_annotation = self._get_mapping_annotation(http_method, api_path)
        
        # 生成方法签名 - 🔧 修复：使用驼峰命名
        method_name = self._first_char_lower(interface_name)
        
        # 根据HTTP方法生成参数和返回类型
        if http_method in ["POST", "PUT"]:
            params = f"@RequestBody {self._capitalize_first(interface_name)}Req request"
            return_type = f"{self._capitalize_first(interface_name)}Resp"
        else:
            # GET或DELETE通常使用查询参数
            params = f"@RequestParam Map<String, Object> params"
            return_type = f"{self._capitalize_first(interface_name)}Resp"
        
        # 选择合适的Service调用
        service_call = self._generate_service_call(interface_name, services)
        
        # 生成完整方法
        method_code = f"""
    /**
     * {description if description else interface_name + "接口"}
     */
    {mapping_annotation}
    public ResponseEntity<{return_type}> {method_name}({params}) {{
        try {{
            {return_type} result = {service_call};
            return ResponseEntity.ok(result);
        }} catch (Exception e) {{
            logger.error("处理{interface_name}请求失败", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }}
    }}"""
        
        return method_code
    
    def _get_mapping_annotation(self, http_method: str, api_path: str) -> str:
        """生成映射注解 - 🔧 修复：使用完整API路径"""
        # 如果api_path是完整路径，直接使用；否则使用接口名
        if api_path.startswith('/'):
            path = api_path
        else:
            path = f'/{api_path}'
            
        if http_method == "GET":
            return f'@GetMapping("{path}")'
        elif http_method == "POST":
            return f'@PostMapping("{path}")'
        elif http_method == "PUT":
            return f'@PutMapping("{path}")'
        elif http_method == "DELETE":
            return f'@DeleteMapping("{path}")'
        else:
            return f'@RequestMapping(value = "{path}", method = RequestMethod.{http_method})'
    
    def _capitalize_first(self, text: str) -> str:
        """首字母大写"""
        return text[0].upper() + text[1:] if text else ""
    
    def _first_char_lower(self, text: str) -> str:
        """首字母小写"""
        return text[0].lower() + text[1:] if text else ""
    
    def _generate_service_call(self, interface_name: str, services: List[Dict[str, str]]) -> str:
        """
        生成Service调用代码
        
        Args:
            interface_name: 接口名称
            services: 可用的Service列表
            
        Returns:
            Service调用代码
        """
        if not services:
            # 如果没有Service，生成默认的返回
            return f"new {self._capitalize_first(interface_name)}Resp()"
        
        # 使用第一个可用的Service
        service = services[0]
        service_var = service['variable']
        
        # 生成方法调用
        return f"{service_var}.{interface_name}(params)"
    
    def _add_required_imports(self, content: str, http_method: str) -> str:
        """
        添加必要的import语句
        
        Args:
            content: 原始内容
            http_method: HTTP方法
            
        Returns:
            添加import后的内容
        """
        required_imports = [
            "import org.springframework.http.ResponseEntity;",
            "import org.springframework.http.HttpStatus;",
            "import java.util.Map;"
        ]
        
        # 根据HTTP方法添加特定import
        if http_method == "GET":
            required_imports.append("import org.springframework.web.bind.annotation.GetMapping;")
            required_imports.append("import org.springframework.web.bind.annotation.RequestParam;")
        elif http_method == "POST":
            required_imports.append("import org.springframework.web.bind.annotation.PostMapping;")
            required_imports.append("import org.springframework.web.bind.annotation.RequestBody;")
        elif http_method == "PUT":
            required_imports.append("import org.springframework.web.bind.annotation.PutMapping;")
            required_imports.append("import org.springframework.web.bind.annotation.RequestBody;")
        elif http_method == "DELETE":
            required_imports.append("import org.springframework.web.bind.annotation.DeleteMapping;")
            required_imports.append("import org.springframework.web.bind.annotation.RequestParam;")
        
        # 检查哪些import需要添加
        imports_to_add = []
        for import_stmt in required_imports:
            if import_stmt not in content:
                imports_to_add.append(import_stmt)
        
        if not imports_to_add:
            return content
        
        # 查找import区域
        import_match = self.import_section_pattern.search(content)
        if import_match:
            # 在现有import区域后添加
            insert_pos = import_match.end()
            new_imports = '\n'.join(imports_to_add) + '\n'
            content = content[:insert_pos] + new_imports + content[insert_pos:]
        else:
            # 在package声明后添加
            package_pattern = re.compile(r'package\s+[^;]+;\s*\n')
            package_match = package_pattern.search(content)
            if package_match:
                insert_pos = package_match.end()
                new_imports = '\n' + '\n'.join(imports_to_add) + '\n'
                content = content[:insert_pos] + new_imports + content[insert_pos:]
        
        return content
    
    def _insert_method_before_class_end(self, content: str, method_code: str) -> str:
        """
        在类结束前插入新方法
        
        Args:
            content: 原始内容
            method_code: 方法代码
            
        Returns:
            插入方法后的内容
        """
        # 查找类的最后一个右大括号
        lines = content.split('\n')
        insert_line = -1
        
        # 从后往前查找最后一个只包含}的行
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line == '}':
                insert_line = i
                break
        
        if insert_line != -1:
            # 在找到的位置前插入新方法
            lines.insert(insert_line, method_code)
            lines.insert(insert_line, "")  # 添加空行
            return '\n'.join(lines)
        else:
            # 如果没找到，直接在末尾添加
            return content + "\n" + method_code + "\n}"
    
    def backup_original_file(self, file_path: str, create_backup: bool = False) -> str:
        """
        备份原始文件
        
        Args:
            file_path: 文件路径
            create_backup: 是否创建备份文件（默认为False，避免生成不必要的.backup文件）
            
        Returns:
            备份文件路径
        """
        # 🆕 如果不需要备份，直接返回原文件路径（表示可以安全修改）
        if not create_backup:
            logger.info(f"🚫 跳过文件备份（按配置）: {file_path}")
            return file_path
            
        # 验证原文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"❌ 原文件不存在，无法备份: {file_path}")
            return ""
        
        backup_path = file_path + ".backup"
        
        try:
            # 读取原文件
            with open(file_path, 'r', encoding='utf-8') as src:
                content = src.read()
            
            # 写入备份文件
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(content)
            
            # 验证备份是否成功
            if os.path.exists(backup_path):
                logger.info(f"📝 已备份原始文件: {backup_path}")
                return backup_path
            else:
                logger.error(f"❌ 备份文件创建失败: {backup_path}")
                return ""
            
        except UnicodeDecodeError as e:
            logger.error(f"❌ 读取原文件编码错误: {e}")
            return ""
        except UnicodeEncodeError as e:
            logger.error(f"❌ 备份文件编码错误: {e}")
            return ""
        except PermissionError as e:
            logger.error(f"❌ 权限错误: {e}")
            return ""
        except Exception as e:
            logger.error(f"❌ 备份文件失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return ""
    
    def save_updated_controller(self, file_path: str, updated_content: str, create_backup: bool = False) -> bool:
        """
        保存更新后的Controller文件
        
        Args:
            file_path: 文件路径
            updated_content: 更新后的内容
            create_backup: 是否创建备份文件（默认为False）
            
        Returns:
            是否保存成功
        """
        try:
            # 验证文件路径
            if not os.path.exists(file_path):
                logger.error(f"❌ 目标文件不存在: {file_path}")
                return False
            
            # 验证路径是否可写
            if not os.access(os.path.dirname(file_path), os.W_OK):
                logger.error(f"❌ 目录不可写: {os.path.dirname(file_path)}")
                return False
            
            # 🆕 可选择性备份原始文件
            if create_backup:
                backup_path = self.backup_original_file(file_path, create_backup=True)
                if not backup_path:
                    logger.error(f"❌ 备份文件失败，取消保存操作: {file_path}")
                    return False
            else:
                logger.info(f"🚫 跳过文件备份，直接更新: {file_path}")
            
            # 写入更新后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            # 验证写入是否成功
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    saved_content = f.read()
                if len(saved_content) == len(updated_content):
                    logger.info(f"✅ 已保存更新后的Controller文件: {file_path}")
                    return True
                else:
                    logger.error(f"❌ 文件写入验证失败，内容长度不匹配")
                    return False
            else:
                logger.error(f"❌ 文件保存后不存在: {file_path}")
                return False
            
        except UnicodeEncodeError as e:
            logger.error(f"❌ 编码错误，可能包含特殊字符: {e}")
            return False
        except PermissionError as e:
            logger.error(f"❌ 权限错误: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 保存Controller文件失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return False
    
    def cleanup_backup_files(self, project_path: str) -> int:
        """
        清理项目中的所有备份目录
        
        Args:
            project_path: 项目路径
            
        Returns:
            清理的文件数量
        """
        cleaned_count = 0
        
        try:
            import glob
            import os
            import shutil
            
            # 查找backup目录下的所有strategy1_backup_*目录
            backup_dir = os.path.join(project_path, "backup")
            if os.path.exists(backup_dir):
                backup_dirs = glob.glob(os.path.join(backup_dir, "strategy1_backup_*"))
                
                for backup_dir_path in backup_dirs:
                    if os.path.isdir(backup_dir_path):
                        try:
                            shutil.rmtree(backup_dir_path)
                            logger.info(f"🗑️ 已清理备份目录: {backup_dir_path}")
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ 无法删除备份目录 {backup_dir_path}: {e}")
            
            # 同时清理旧的.backup文件（向后兼容）
            backup_files = glob.glob(os.path.join(project_path, "**", "*.backup"), recursive=True)
            
            for backup_file in backup_files:
                try:
                    os.remove(backup_file)
                    logger.info(f"🗑️ 已清理备份文件: {backup_file}")
                    cleaned_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ 无法删除备份文件 {backup_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"✅ 总共清理了 {cleaned_count} 个备份文件")
            else:
                logger.info("ℹ️ 没有找到需要清理的备份文件")
                
        except Exception as e:
            logger.error(f"❌ 清理备份文件失败: {e}")
            
        return cleaned_count 