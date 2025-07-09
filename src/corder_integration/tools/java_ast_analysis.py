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
