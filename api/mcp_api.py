# coding: utf-8
"""
MCP (Model Context Protocol) API
标准化的工具调用接口
"""
from flask import Blueprint, request, jsonify
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.agent.mcp_protocol import MCPServer, MCPRequest

mcp_bp = Blueprint('mcp', __name__, url_prefix='/mcp')

# MCP服务器单例
_mcp_server = None

def get_mcp_server():
    """获取MCP服务器单例"""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server

@mcp_bp.route('/', methods=['POST'])
def handle_mcp_request():
    """
    MCP请求入口
    所有MCP请求都通过此端点处理
    """
    try:
        # 解析JSON-RPC请求
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }), 400
        
        # 处理请求
        server = get_mcp_server()
        response = server.handle_request(request_data)
        
        return jsonify(response.to_dict())
    
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }), 500

@mcp_bp.route('/tools', methods=['GET'])
def list_tools():
    """列出所有可用工具（便捷接口）"""
    server = get_mcp_server()
    tools = [tool.to_dict() for tool in server.tools.values()]
    return jsonify({
        "success": True,
        "tools": tools
    })

@mcp_bp.route('/tools/<tool_name>', methods=['POST'])
def call_tool(tool_name):
    """
    直接调用工具（便捷接口，非标准MCP）
    用于简单的HTTP调用场景
    """
    try:
        arguments = request.get_json() or {}
        
        # 构造MCP请求
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # 处理请求
        server = get_mcp_server()
        response = server.handle_request(mcp_request)
        
        return jsonify(response.to_dict())
    
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }), 500
