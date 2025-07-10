from langchain.tools import tool
import javalang

@tool
def parse_ast_tool(code: str) -> dict:
    """
    将Java源码解析为AST结构（Python对象转dict）
    """
    try:
        tree = javalang.parse.parse(code)
        result = {
            "package": tree.package.name if tree.package else None,
            "imports": [imp.path for imp in tree.imports],
            "types": []
        }
        for type_decl in tree.types:
            result["types"].append({
                "name": type_decl.name,
                "kind": type(type_decl).__name__,
                "fields": [field.declarators[0].name for field in type_decl.fields],
                "methods": [method.name for method in type_decl.methods],
                "annotations": [anno.name for anno in type_decl.annotations],
                "extends": type_decl.extends.name if type_decl.extends else None,
                "implements": [impl.name for impl in type_decl.implements] if type_decl.implements else []
            })
        return result
    except Exception as e:
        return {"error": str(e)}
    

@tool
def extract_class_info_tool(ast: dict) -> dict:
    """
    从AST JSON中提取类信息（适合LLM阅读）
    """
    classes = []
    for type_node in ast.get("types", []):
        classes.append({
            "className": type_node["name"],
            "fields": type_node["fields"],
            "methods": type_node["methods"],
            "annotations": type_node["annotations"],
            "extends": type_node["extends"],
            "implements": type_node["implements"]
        })
    return {"classes": classes, "package": ast.get("package")}

@tool
def package_structure_tool(file_paths: list) -> dict:
    """
    根据文件路径提取包结构和类名映射。
    """
    structure = {}
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = javalang.parse.parse(f.read())
                package = tree.package.name if tree.package else "default"
                for type_decl in tree.types:
                    class_name = type_decl.name
                    if package not in structure:
                        structure[package] = []
                    structure[package].append(class_name)
            except Exception as e:
                structure[file_path] = f"Parse error: {e}"
    return structure

@tool
def dependency_analysis_tool(ast: dict) -> dict:
    """
    分析类中的注解依赖（如@Service, @Autowired）
    """
    dependencies = []
    for cls in ast.get("types", []):
        for anno in cls.get("annotations", []):
            if anno in ["Service", "Component", "Repository"]:
                dependencies.append({"class": cls["name"], "type": anno})
        # 粗略识别字段依赖（如@Autowired字段）
        for field in cls.get("fields", []):
            if "repo" in field.lower() or "client" in field.lower():
                dependencies.append({"class": cls["name"], "field": field})
    return {"dependencies": dependencies}

@tool
def generate_uml_tool(ast: dict) -> str:
    """
    将类结构转换为Mermaid格式类图
    """
    lines = ["classDiagram"]
    for cls in ast.get("types", []):
        class_name = cls["name"]
        lines.append(f"class {class_name} {{")
        for field in cls["fields"]:
            lines.append(f"  +{field}")
        for method in cls["methods"]:
            lines.append(f"  +{method}()")
        lines.append("}")
        if cls["extends"]:
            lines.append(f"{cls['extends']} <|-- {class_name}")
        for iface in cls["implements"]:
            lines.append(f"{iface} <|.. {class_name}")
    return "\n".join(lines)