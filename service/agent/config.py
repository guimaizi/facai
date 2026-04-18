# coding: utf-8
"""
Agent配置管理
"""
import os
import json
import logging

class AgentConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logger = logging.getLogger()
        self.Path = os.path.dirname(__file__).replace('\\', '/')
        self.config_file = os.path.join(self.Path, 'agent_config.json')
        self.config = self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """加载配置文件"""
        default_config = {
            "models": {
                "ollama": {
                    "enabled": True,
                    "base_url": "http://localhost:11434",
                    "model": "nemotron-cascade-2:30b",
                    "timeout": 60
                },
                "zhipu": {
                    "enabled": True,
                    "api_key": "",
                    "model": "glm-4",
                    "base_url": "https://open.bigmodel.cn/api/paas/v4",
                    "timeout": 60
                },
                "qianwen": {
                    "enabled": True,
                    "api_key": "",
                    "model": "qwen-coder-plus",
                    "base_url": "https://dashscope.aliyuncs.com/api/v1",
                    "timeout": 60
                },
                "openai": {
                    "enabled": True,
                    "api_key": "lBa7DF45b9xCVIqIZi7AYZEL43esNTnp",
                    "model": "gpt-5.4",
                    "base_url": "https://molungpt.com/v1",
                    "timeout": 60
                },
                "gemini": {
                    "enabled": True,
                    "api_key": "",
                    "model": "gemini-pro",
                    "base_url": "https://generativelanguage.googleapis.com/v1beta",
                    "timeout": 60
                }
            },
            "default_model": "openai",
            "max_tokens": 4096,
            "temperature": 0.7,
            "audit_settings": {
                "max_file_size": 1024 * 1024,  # 1MB
                "max_code_length": 50000,  # 最大代码长度（字符数）
                "chunk_size": 20000,  # 如果需要分块，每块大小
                "supported_extensions": [
                    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".php", 
                    ".go", ".rb", ".c", ".cpp", ".h", ".cs", ".swift",
                    ".kt", ".rs", ".sql", ".sh", ".bat"
                ],
                "exclude_dirs": [
                    "node_modules", "__pycache__", ".git", "venv",
                    "build", "dist", ".idea", "vendor"
                ]
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置
                    self._deep_update(default_config, loaded_config)
            except Exception as e:
                self.logger.error(f"加载agent配置失败: {str(e)}")
        
        return default_config
    
    def _deep_update(self, base, update):
        """深度合并字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"保存agent配置失败: {str(e)}")
            return False
    
    def get_model_config(self, model_name):
        """获取指定模型的配置"""
        return self.config.get('models', {}).get(model_name)
    
    def set_model_config(self, model_name, config):
        """设置模型配置"""
        if 'models' not in self.config:
            self.config['models'] = {}
        self.config['models'][model_name] = config
        return self.save_config()
    
    def get_default_model(self):
        """获取默认模型名称"""
        return self.config.get('default_model', 'ollama')
    
    def set_default_model(self, model_name):
        """设置默认模型"""
        self.config['default_model'] = model_name
        return self.save_config()
    
    def get_audit_settings(self):
        """获取审计设置"""
        return self.config.get('audit_settings', {})
