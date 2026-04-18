# Agent代码审计系统完整文档

## 目录

- [1. 快速开始](#1-快速开始)
- [2. 功能介绍](#2-功能介绍)
- [3. 架构设计](#3-架构设计)
- [4. 模型安装配置](#4-模型安装配置)
- [5. 使用方法](#5-使用方法)
- [6. API接口](#6-api接口)
- [7. 高级功能](#7-高级功能)

---

## 1. 快速开始

### 1.1 安装依赖

```bash
# 核心依赖（必需）
pip install openai

# 或一次性安装所有依赖
pip install -r requirements.txt
```

### 1.2 基础使用

```python
from service.agent import AgentCore

# 初始化Agent（使用默认模型）
agent = AgentCore()

# 测试连接
success, message = agent.test_connection()
print(f"连接测试: {message}")

# 审计代码片段
code = """
import os
user_input = input("Enter command: ")
os.system(user_input)  # 命令注入漏洞
"""

result = agent.audit_code(code, language="python")
print(result)
```

---

## 2. 功能介绍

### 2.1 核心功能

**代码安全审计Agent**是一个智能化的代码安全审计系统，支持多种AI模型，能够自动检测代码中的安全漏洞。

**核心特性**：
- ✅ 只关注高危害漏洞（8种）
- ✅ 标准JSON输出格式
- ✅ 流式输出支持
- ✅ 多模型支持（Ollama、智谱、千问、GPT、Gemini）
- ✅ MCP协议标准

### 2.2 支持的漏洞类型

| 漏洞类型 (英文) | 中文名称 | 危害等级 |
|----------------|---------|---------|
| SQL Injection | SQL注入 | high |
| XSS | 跨站脚本 | high |
| Code Injection | 代码注入 | high |
| Command Injection | 命令注入 | high |
| SSRF | 服务端请求伪造 | high |
| AKSK Leak | 密钥硬编码 | high |
| Arbitrary File Operation | 任意文件操作 | high |
| Path Traversal | 路径遍历 | high |

### 2.3 输出格式

#### 标准JSON输出

**Vulnerability Object**:
```json
{
  "vulnerability_type": "SQL Injection",
  "severity": "high",
  "code_snippet": "query = f'SELECT * FROM users WHERE id={user_id}'"
}
```

**字段说明**:

| 字段 | 类型 | 描述 | 值 |
|-----|------|------|-----|
| `vulnerability_type` | string | 漏洞类型(英文) | 见下表 |
| `severity` | string | 危害等级 | `high`, `medium`, `low` |
| `code_snippet` | string | 漏洞代码片段 | 代码字符串 |

**支持的漏洞类型**:

| vulnerability_type | 中文 | 描述 |
|-------------------|------|------|
| SQL Injection | SQL注入 | 数据库注入漏洞 |
| XSS | 跨站脚本 | 跨站脚本攻击 |
| Code Injection | 代码注入 | eval/exec/反序列化 |
| Command Injection | 命令注入 | 操作系统命令执行 |
| SSRF | 服务端请求伪造 | 服务端请求伪造 |
| AKSK Leak | AKSK泄露 | 硬编码API密钥 |
| Arbitrary File Read | 任意文件读取 | 未授权文件读取 |
| Arbitrary File Write | 任意文件写入 | 未授权文件写入 |
| Arbitrary File Upload | 任意文件上传 | 未授权文件上传 |
| Path Traversal | 路径遍历 | 目录遍历 |

#### 输出示例

**单个漏洞**:
```json
[
  {
    "vulnerability_type": "Command Injection",
    "severity": "high",
    "code_snippet": "os.system(user_input)"
  }
]
```

**多个漏洞**:
```json
[
  {
    "vulnerability_type": "SQL Injection",
    "severity": "high",
    "code_snippet": "query = f'SELECT * FROM users WHERE id={user_id}'"
  },
  {
    "vulnerability_type": "Command Injection",
    "severity": "high",
    "code_snippet": "os.system(user_input)"
  },
  {
    "vulnerability_type": "XSS",
    "severity": "high",
    "code_snippet": "element.innerHTML = userInput"
  }
]
```

**无漏洞**:
```json
[]
```

#### 危害等级

| 等级 | 描述 | 处理要求 |
|-----|------|---------|
| `high` | 严重漏洞 | 必须立即修复 |
| `medium` | 中等风险 | 建议修复 |
| `low` | 低风险 | 可选修复 |

---

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Flask API Layer                       │
│                  (api/agent_api.py)                     │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 Agent Core Layer                         │
│             (agent/agent_core.py)                       │
│  ┌──────────────────────────────────────────────┐       │
│  │  - 单例模式管理                                │       │
│  │  - 任务调度                                   │       │
│  │  - 结果存储                                   │       │
│  │  - 模型切换                                   │       │
│  └──────────────────────────────────────────────┘       │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐      ┌────────▼─────────┐
│  Code Analyzer │      │   Config Manager │
│                │      │                  │
│ - 文件分析     │      │ - 模型配置       │
│ - 代码分析     │      │ - 审计设置       │
│ - 项目分析     │      │ - 单例管理       │
└───────┬────────┘      └──────────────────┘
        │
┌───────▼────────────────────────────────────────────────┐
│                  Model Layer (模型层)                    │
├─────────────────────────────────────────────────────────┤
│  Base Model (抽象基类)                                   │
│  - chat()         发送聊天请求                           │
│  - test_connection() 测试连接                           │
│  - analyze_code() 分析代码                              │
├──────────┬──────────┬──────────┬──────────┬────────────┤
│  Ollama  │  Zhipu   │ Qianwen  │  OpenAI  │   Gemini   │
│  (本地)  │  (智谱)   │  (千问)   │  (GPT)   │  (Google)  │
└──────────┴──────────┴──────────┴──────────┴────────────┘
```

### 3.2 模块说明

#### 配置层 (config.py)
- 管理所有模型的配置信息
- 管理审计设置（文件大小限制、支持的语言等）
- 单例模式，全局唯一配置实例

#### 模型层 (models/)
**设计理念**: 优先使用官方SDK，自动回退OpenAI兼容模式

**策略流程**:
```
初始化模型
    ↓
检测官方SDK
    ├─ 已安装 → 使用官方SDK
    │   ├─ 优势：更稳定、功能全、官方支持
    │   └─ 示例：zhipuai.ZhipuAI()
    │
    └─ 未安装 → 使用OpenAI兼容
        ├─ 优势：统一接口、减少依赖
        └─ 示例：OpenAI(base_url=模型API地址)
```

**各模型实现**:
- **ollama.py**: Ollama本地模型
  - 优先：`ollama` 官方SDK
  - 回退：OpenAI兼容模式
  - 特点：完全免费、离线运行
  
- **zhipu.py**: 智谱AI
  - 优先：`zhipuai.ZhipuAI` 官方SDK
  - 回退：OpenAI兼容模式
  - 模型：GLM-4、GLM-3-turbo
  
- **qianwen.py**: 阿里云千问
  - 优先：`dashscope.Generation` 官方SDK
  - 回退：OpenAI兼容模式
  - 模型：qwen-coder-plus、qwen-plus
  
- **openai.py**: OpenAI GPT
  - 仅使用：`openai.OpenAI` 官方SDK
  - 模型：gpt-4-turbo、gpt-3.5-turbo
  
- **gemini.py**: Google Gemini
  - 优先：`google.generativeai` 官方SDK
  - 回退：OpenAI兼容模式
  - 模型：gemini-pro、gemini-pro-vision

#### 提示词层 (prompts/)
- 针对不同语言定制专属提示词
- 简化输出格式（只检测8种高危害漏洞）
- 标准JSON输出

#### 分析器层 (code_analyzer.py)
- 单文件分析
- 代码片段分析
- 项目目录分析
- 语言自动检测

#### 核心调度层 (agent_core.py)
- 统一的入口管理
- 任务调度和协调
- 结果持久化存储
- 模型切换管理

### 3.3 数据流

**代码审计流程**:
```
用户输入代码
    ↓
API层接收请求
    ↓
Agent核心调度器
    ↓
Code Analyzer分析器
    ↓
验证输入有效性
    ↓
检测编程语言
    ↓
获取对应提示词
    ↓
构建消息列表
    ↓
调用模型API
    ↓
解析返回结果
    ↓
保存审计记录
    ↓
返回给用户
```

---

## 4. 模型安装配置

### 4.1 Ollama（本地模型，免费）

**安装Ollama**:
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 从 https://ollama.com/download 下载安装包
```

**启动服务并拉取模型**:
```bash
# 启动服务
ollama serve

# 拉取代码审计模型（推荐）
ollama pull codellama:latest
ollama pull deepseek-coder:latest
ollama pull qwen3.5:9b
```

**Python依赖（可选）**:
```bash
pip install ollama  # 官方SDK，不装也能用OpenAI兼容模式
```

### 4.2 智谱AI（推荐）

**获取API Key**:
1. 访问 https://open.bigmodel.cn/
2. 注册账号并登录
3. 在控制台获取API Key

**安装SDK**:
```bash
pip install zhipuai
```

**配置**:
编辑 `service/agent/agent_config.json`:
```json
{
  "models": {
    "zhipu": {
      "enabled": true,
      "api_key": "your_api_key_here",
      "model": "glm-4"
    }
  }
}
```

### 4.3 阿里云千问

**获取API Key**:
1. 访问 https://dashscope.aliyun.com/
2. 开通服务并获取API Key

**安装SDK**:
```bash
pip install dashscope
```

**配置**:
```json
{
  "models": {
    "qianwen": {
      "enabled": true,
      "api_key": "your_api_key_here",
      "model": "qwen-coder-plus"
    }
  }
}
```

### 4.4 OpenAI GPT-4

**获取API Key**:
1. 访问 https://platform.openai.com/
2. 获取API Key

**安装SDK**:
```bash
pip install openai  # 已包含在基础依赖中
```

**配置**:
```json
{
  "models": {
    "openai": {
      "enabled": true,
      "api_key": "sk-xxxxx",
      "model": "gpt-4-turbo"
    }
  }
}
```

### 4.5 Google Gemini

**获取API Key**:
1. 访问 https://makersuite.google.com/app/apikey
2. 创建API Key

**安装SDK**:
```bash
pip install google-generativeai
```

**配置**:
```json
{
  "models": {
    "gemini": {
      "enabled": true,
      "api_key": "your_api_key_here",
      "model": "gemini-pro"
    }
  }
}
```

### 4.6 完整配置示例

```json
{
  "models": {
    "ollama": {
      "enabled": true,
      "base_url": "http://localhost:11434",
      "model": "qwen3.5:9b",
      "timeout": 60
    },
    "zhipu": {
      "enabled": true,
      "api_key": "your_api_key_here",
      "model": "glm-4",
      "base_url": "https://open.bigmodel.cn/api/paas/v4",
      "timeout": 60
    },
    "qianwen": {
      "enabled": true,
      "api_key": "your_api_key_here",
      "model": "qwen-coder-plus",
      "base_url": "https://dashscope.aliyun.com/api/v1",
      "timeout": 60
    },
    "openai": {
      "enabled": true,
      "api_key": "your_openai_key",
      "model": "gpt-4-turbo",
      "base_url": "https://api.openai.com/v1",
      "timeout": 60
    },
    "gemini": {
      "enabled": true,
      "api_key": "your_gemini_key",
      "model": "gemini-pro",
      "base_url": "https://generativelanguage.googleapis.com/v1beta",
      "timeout": 60
    }
  },
  "default_model": "ollama",
  "audit_settings": {
    "max_file_size": 1048576,
    "max_code_length": 50000,
    "supported_extensions": [".py", ".js", ".java", ".php"],
    "exclude_dirs": ["node_modules", "__pycache__", ".git"]
  }
}
```

### 4.7 模型推荐

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 开发测试 | Ollama | 免费、离线、隐私 |
| 生产环境 | 智谱AI | 中文好、性价比高 |
| 关键审计 | GPT-4 | 能力最强 |
| 性价比 | 千问 | 代码能力强、便宜 |
| 多模态 | Gemini | 支持图像输入 |

---

## 5. 使用方法

### 5.1 审计代码（流式输出，推荐）

```python
from service.agent import AgentCore

agent = AgentCore()

code = """
import os
user_input = input("Enter command: ")
os.system(user_input)  # 命令注入漏洞
"""

# 流式输出 - 实时看到内容
result = agent.audit_code_stream(code, language="python")

if result['success']:
    # 实时打印每个chunk
    for chunk in result['result']:
        print(chunk, end='', flush=True)
    print()  # 换行
```

**优势**：
- ✅ 实时看到审计进度
- ✅ 不需要等待完整响应
- ✅ 更好的用户体验

### 5.2 审计代码（非流式）

```python
from service.agent import AgentCore

agent = AgentCore()

code = """
import os
os.system(input())
"""

# 非流式 - 等待完整响应
result = agent.audit_code(code, language="python")

if result['success']:
    # 结果是标准JSON格式
    for vuln in result['result']['vulnerabilities']:
        print(f"Type: {vuln['vulnerability_type']}")
        print(f"Severity: {vuln['severity']}")
        print(f"Code: {vuln['code_snippet']}")
else:
    print(f"错误: {result['error']}")
```

### 5.3 审计单个文件

```python
from service.agent import AgentCore

agent = AgentCore()

# 审计单个Python文件
result = agent.audit_file("path/to/vulnerable_code.py")

if result['success']:
    print("审计结果:")
    print(result['result'])
else:
    print(f"审计失败: {result['error']}")
```

### 5.4 审计整个项目

```python
from service.agent import AgentCore

agent = AgentCore()

# 审计整个项目目录
result = agent.audit_project(
    project_path="/path/to/project",
    recursive=True  # 递归扫描
)

print(f"总文件数: {result['total_files']}")
print(f"成功分析: {result['analyzed_files']}")
print(f"失败文件: {result['failed_files']}")

# 查看摘要
if 'summary' in result:
    print(f"摘要: {result['summary']}")
```

### 5.5 使用不同模型

```python
from service.agent import AgentCore

# 使用Ollama本地模型（推荐用于开发测试）
agent = AgentCore(model_name="ollama")

# 使用智谱AI（推荐用于生产环境）
agent = AgentCore(model_name="zhipu")

# 使用OpenAI GPT-4（推荐用于关键审计）
agent = AgentCore(model_name="openai")

# 使用阿里云千问（性价比高）
agent = AgentCore(model_name="qianwen")

# 使用Google Gemini（多模态支持）
agent = AgentCore(model_name="gemini")

# 动态切换模型
agent.change_model("gemini")
```

### 5.6 支持的语言

- Python (.py) ✅
- JavaScript (.js, .jsx) ✅
- TypeScript (.ts, .tsx) ✅
- Java (.java) ✅
- PHP (.php) ✅
- Go (.go) ✅
- Ruby (.rb) ✅
- C/C++ (.c, .cpp, .h) ✅
- C# (.cs) ✅
- Swift (.swift) ✅
- Kotlin (.kt) ✅
- Rust (.rs) ✅
- SQL (.sql) ✅
- Shell (.sh, .bat) ✅

---

## 6. API接口

### 6.1 获取Agent状态

```bash
curl http://localhost:5001/api/agent/status
```

### 6.2 测试模型连接

```bash
curl -X POST http://localhost:5001/api/agent/test_connection \
  -H "Content-Type: application/json" \
  -d '{"model": "ollama"}'
```

### 6.3 审计代码（非流式）

```bash
curl -X POST http://localhost:5001/api/agent/audit/code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import os\nos.system(input())",
    "language": "python",
    "model": "ollama",
    "stream": false
  }'
```

**完整响应示例**:

**Python API**:
```python
result = agent.audit_code(code, "python")

# Result structure
{
  "vulnerabilities": [
    {
      "vulnerability_type": "SQL Injection",
      "severity": "high",
      "code_snippet": "..."
    }
  ],
  "total": 1,
  "format": "json"
}
```

**MCP API**:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"vulnerability_type\":\"SQL Injection\",\"severity\":\"high\",\"code_snippet\":\"...\"}]"
      }
    ],
    "isError": false
  }
}
```

### 6.4 审计代码（流式输出）

```bash
curl -X POST http://localhost:5001/api/agent/audit/code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import os\nos.system(input())",
    "language": "python",
    "model": "ollama",
    "stream": true
  }'
```

**流式响应格式**（Server-Sent Events）:
```
data: {"content": "## 安全漏洞汇总\n"}

data: {"content": "发现"}

data: {"content": " 3 个漏洞"}

data: [DONE]
```

### 6.5 审计项目

```bash
curl -X POST http://localhost:5001/api/agent/audit/project \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/project",
    "recursive": true,
    "model": "zhipu"
  }'
```

### 6.6 集成示例

**Python**:
```python
from service.agent import AgentCore

agent = AgentCore()
result = agent.audit_code(code, "python")

for vuln in result['vulnerabilities']:
    print(f"Type: {vuln['vulnerability_type']}")
    print(f"Severity: {vuln['severity']}")
    print(f"Code: {vuln['code_snippet']}")
```

**JavaScript**:
```javascript
const result = await agent.auditCode(code, "python");

result.vulnerabilities.forEach(vuln => {
    console.log(`Type: ${vuln.vulnerability_type}`);
    console.log(`Severity: ${vuln.severity}`);
    console.log(`Code: ${vuln.code_snippet}`);
});
```

**cURL**:
```bash
curl -X POST http://localhost:5001/mcp/tools/audit_code \
  -H "Content-Type: application/json" \
  -d '{"code":"...","language":"python"}'
```

---

## 7. 高级功能

### 7.1 与CI/CD集成

```yaml
# .github/workflows/security.yml
name: Security Audit
on: [push]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Security Audit
        run: |
          python -c "
          from service.agent import AgentCore
          agent = AgentCore()
          result = agent.audit_project('.')
          if result['total'] > 0:
            print('发现漏洞!')
            exit(1)
          "
```

### 7.2 生成报告

```python
from service.agent import AgentCore
import json

agent = AgentCore()
result = agent.audit_code(code, "python")

# 保存JSON报告
with open('audit_report.json', 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# 生成Markdown报告
md = "# Security Audit Report\n\n"
md += f"Found {result['result']['total']} vulnerabilities\n\n"

for vuln in result['result']['vulnerabilities']:
    md += f"## {vuln['vulnerability_type']}\n"
    md += f"- **Severity**: {vuln['severity']}\n"
    md += f"- **Code**: `{vuln['code_snippet']}`\n\n"

with open('audit_report.md', 'w') as f:
    f.write(md)
```

### 7.3 程序中修改配置

```python
from service.agent.config import AgentConfig

config = AgentConfig()

# 设置模型API Key
config.set_model_config('zhipu', {
    "enabled": True,
    "api_key": "your_key",
    "model": "glm-4",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "timeout": 60
})

# 设置默认模型
config.set_default_model('zhipu')
```

### 7.4 批量文件审计

```python
import os
from service.agent import AgentCore

agent = AgentCore()

# 遍历项目目录
for root, dirs, files in os.walk('project/'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            result = agent.audit_file(filepath)
            
            if result['success'] and result['result']['total'] > 0:
                print(f"{filepath}: {result['result']['total']} 个漏洞")
```

---

## 8. 故障排查

### 8.1 Ollama连接失败

```bash
# 确保Ollama服务正在运行
ollama serve

# 拉取模型
ollama pull qwen3.5:9b

# 或安装Python SDK（可选）
pip install ollama
```

### 8.2 API Key无效

- 检查配置文件中的API Key是否正确
- 检查API Key是否有足够的配额
- 确认API Key对应的模型是否可用

### 8.3 SDK相关问题

```bash
# 如果遇到SDK问题，可以卸载后使用OpenAI兼容模式
pip uninstall ollama zhipuai dashscope google-generativeai

# 系统会自动回退到OpenAI兼容模式
# 大多数模型都支持OpenAI格式
```

### 8.4 超时问题

- 增加配置中的timeout值
- 减少分析的代码量
- 使用更快的模型

---

## 9. 注意事项

1. **API Key安全**: 不要将API Key提交到代码仓库
2. **文件大小**: 默认限制1MB，可在配置中调整
3. **代码长度**: 默认限制50000字符，超出会自动截断
4. **超时设置**: 复杂代码分析可能需要更长时间
5. **并发限制**: 注意各模型的并发限制和费用
6. **结果保存**: 审计结果自动保存在 `project_data/audit_results/`

---

## 10. 核心优化

### 10.1 防止模型被代码内容干扰

**关键措施**：
1. **Temperature = 0.0** - 完全确定性输出
2. **强制JSON格式** - `format='json'` (Ollama) / `response_format={"type": "json_object"}` (OpenAI)
3. **限制输出长度** - `max_tokens=2048`
4. **代码长度限制** - 最大50000字符

**原理**：
```
高Temperature (0.7) → 模型"自由发挥" → 被代码内容干扰
低Temperature (0.0) → 模型"严格执行" → 只输出JSON
```

### 10.2 提示词优化

**简洁明确的提示词结构**：
```
你是代码安全审计工具。

任务：检测代码中的安全漏洞。

检测类型：SQL注入、XSS、代码注入、命令注入、SSRF、密钥泄露、任意文件操作、路径遍历。

输出格式：
[
  {
    "vulnerability_type": "漏洞类型",
    "severity": "high/medium/low",
    "code_snippet": "问题代码"
  }
]

规则：
1. 只输出JSON数组
2. 无漏洞输出：[]
3. 禁止输出任何其他文字、说明或解释

用户会发送代码，你直接返回JSON结果。
```

---

## 11. 最佳实践

1. **始终解析为JSON数组** - 响应始终是数组
2. **检查数组长度** - 空数组表示无漏洞
3. **使用英文字段名** - 专业且标准
4. **基于严重性排序** - 优先修复高危问题

---

## 12. 总结

该Agent架构设计遵循了以下原则：

1. **模块化**: 各层职责清晰，易于维护
2. **可扩展**: 轻松添加新模型、新功能
3. **易用性**: 统一的API接口，简单的调用方式
4. **稳定性**: 完善的错误处理和验证机制
5. **高性能**: 单例模式、连接复用、批量处理
6. **标准化**: 支持MCP协议，JSON标准输出

这种设计既满足了当前需求，又为未来扩展留下了充足空间。
