import asyncio
import json
import logging
from typing import Set
import websockets
from websockets.server import WebSocketServerProtocol
from datetime import datetime
import uuid

# 导入现有的分析器
from enhanced_analyzer import EnhancedAnalyzer
from config import Settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketChatServer:
    def __init__(self):
        self.settings = Settings()
        self.analyzer = EnhancedAnalyzer()
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        
    async def register_client(self, websocket: WebSocketServerProtocol):
        """注册新客户端"""
        self.connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"客户端 {client_id} 已连接，当前连接数: {len(self.connected_clients)}")
        
        # 发送欢迎消息
        welcome_message = {
            "type": "system",
            "message": "欢迎使用 analyDesign 智能分析助手！",
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        await websocket.send(json.dumps(welcome_message, ensure_ascii=False))

    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """注销客户端"""
        self.connected_clients.discard(websocket)
        client_id = id(websocket)
        logger.info(f"客户端 {client_id} 已断开，当前连接数: {len(self.connected_clients)}")

    async def process_message(self, websocket: WebSocketServerProtocol, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type", "chat")
            user_message = data.get("message", "")
            message_id = data.get("message_id", str(uuid.uuid4()))
            
            logger.info(f"收到消息: {user_message[:50]}...")
            
            if message_type == "chat":
                await self.handle_chat_message(websocket, user_message, message_id)
            elif message_type == "file_upload":
                await self.handle_file_upload(websocket, data)
            elif message_type == "ping":
                await self.handle_ping(websocket)
                
        except json.JSONDecodeError:
            error_response = {
                "type": "error",
                "message": "无效的 JSON 格式",
                "timestamp": datetime.now().isoformat(),
                "message_id": str(uuid.uuid4())
            }
            await websocket.send(json.dumps(error_response, ensure_ascii=False))
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}")
            error_response = {
                "type": "error",
                "message": f"服务器错误: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "message_id": str(uuid.uuid4())
            }
            await websocket.send(json.dumps(error_response, ensure_ascii=False))

    async def handle_chat_message(self, websocket: WebSocketServerProtocol, user_message: str, message_id: str):
        """处理聊天消息"""
        # 发送正在处理的状态
        processing_response = {
            "type": "processing",
            "message": "正在分析您的问题...",
            "timestamp": datetime.now().isoformat(),
            "message_id": message_id,
            "status": "thinking"
        }
        await websocket.send(json.dumps(processing_response, ensure_ascii=False))
        
        try:
            # 使用分析器处理消息
            analysis_result = await self.analyzer.analyze_async(user_message)
            
            # 发送分析结果
            response = {
                "type": "chat_response",
                "message": analysis_result.get("response", "抱歉，我无法处理您的请求。"),
                "analysis": analysis_result,
                "timestamp": datetime.now().isoformat(),
                "message_id": message_id,
                "status": "completed"
            }
            await websocket.send(json.dumps(response, ensure_ascii=False))
            
        except Exception as e:
            logger.error(f"分析消息时出错: {str(e)}")
            error_response = {
                "type": "error",
                "message": "分析过程中出现错误，请稍后重试。",
                "timestamp": datetime.now().isoformat(),
                "message_id": message_id,
                "status": "error"
            }
            await websocket.send(json.dumps(error_response, ensure_ascii=False))

    async def handle_file_upload(self, websocket: WebSocketServerProtocol, data: dict):
        """处理文件上传"""
        file_info = data.get("file_info", {})
        file_name = file_info.get("name", "unknown")
        
        response = {
            "type": "file_response",
            "message": f"文件 {file_name} 上传成功，正在处理...",
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        await websocket.send(json.dumps(response, ensure_ascii=False))

    async def handle_ping(self, websocket: WebSocketServerProtocol):
        """处理心跳检测"""
        pong_response = {
            "type": "pong",
            "timestamp": datetime.now().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        await websocket.send(json.dumps(pong_response, ensure_ascii=False))

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("客户端连接已关闭")
        except Exception as e:
            logger.error(f"处理客户端连接时出错: {str(e)}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self, host: str = "localhost", port: int = 8765):
        """启动 WebSocket 服务器"""
        logger.info(f"启动 WebSocket 服务器: ws://{host}:{port}")
        
        async with websockets.serve(
            self.handle_client,
            host,
            port,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ):
            logger.info("WebSocket 服务器已启动，等待连接...")
            await asyncio.Future()  # 保持服务器运行

# 扩展分析器以支持异步操作
class EnhancedAnalyzer:
    def __init__(self):
        # 这里可以初始化您的分析器
        pass
    
    async def analyze_async(self, message: str) -> dict:
        """异步分析消息"""
        # 模拟分析过程
        await asyncio.sleep(1)  # 模拟处理时间
        
        # 这里应该调用您现有的分析逻辑
        return {
            "response": f"我理解您的问题：{message}\n\n基于我的分析，这是一个关于产品设计的询问。我建议从用户需求、市场定位和技术可行性三个维度来考虑这个问题。",
            "confidence": 0.85,
            "analysis_type": "product_design",
            "suggestions": [
                "深入了解目标用户群体",
                "分析竞品功能特点", 
                "评估技术实现难度"
            ]
        }

if __name__ == "__main__":
    server = WebSocketChatServer()
    asyncio.run(server.start_server()) 