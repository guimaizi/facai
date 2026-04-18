#!/usr/bin/env python3
# coding: utf-8
"""
MCP Server - 用于Claude Desktop集成
通过标准输入/输出进行MCP通信
"""
import sys
import os
import json

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from service.agent.mcp_protocol import MCPServer

def main():
    """MCP服务器主循环"""
    # 初始化MCP服务器
    server = MCPServer(
        name="code-audit-agent",
        version="1.0.0"
    )
    
    # 记录到文件（不影响stdout）
    log_file = os.path.join(project_root, 'project_data', 'mcp.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    def log(message):
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
    
    log("MCP Server started")
    
    # 读取标准输入，处理请求
    for line in sys.stdin:
        try:
            line = line.strip()
            if not line:
                continue
            
            log(f"Received: {line}")
            
            # 解析请求
            request = json.loads(line)
            
            # 处理请求
            response = server.handle_request(request)
            
            # 输出响应
            response_json = json.dumps(response.to_dict())
            print(response_json, flush=True)
            
            log(f"Sent: {response_json}")
            
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
            log(f"Parse error: {str(e)}")
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
            log(f"Internal error: {str(e)}")

if __name__ == "__main__":
    main()
