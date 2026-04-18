# coding: utf-8
"""
漏洞参数去重数据库操作类
@Time :    4/16/2026
@Author:  facai
@File: vuln_param_database.py
@Software: VSCode

功能说明：
1. 存储已扫描的参数信息
2. 查询已扫描的参数列表
3. 用于漏洞扫描参数去重
"""

from .mongodb_handler import MongoDBHandler
from service.Class_Core_Function import Class_Core_Function


class VulnParamDatabase:
    """漏洞参数去重数据库操作类"""
    
    def __init__(self, project_name=None):
        self.Core_Function = Class_Core_Function()
        self.db_handler = MongoDBHandler()
        self.project_name = project_name
        # 使用 project_{name}_vuln_param 表名
        self.collection_name = f"project_{project_name}_vuln_param" if project_name else None
    
    def get_scanned_params(self, url_path, website=None):
        """
        获取指定URL路径已扫描的参数列表
        
        Args:
            url_path: str - URL路径（带泛化，如：http://127.0.0.1/{string-7}）
            website: str - 站点URL（可选，用于更精确的匹配）
        
        Returns:
            set - 已扫描的参数名集合
                {'name', 'id', ...}
        """
        if not self.collection_name:
            return set()
        
        query = {'url_path': url_path}
        
        # 如果指定了website，添加到查询条件
        if website:
            query['website'] = website
        
        # 查询所有匹配的记录
        records = self.db_handler.find(
            self.collection_name,
            query,
            projection={'param_name_list': 1}
        )
        
        # 合并所有已扫描的参数
        scanned_params = set()
        for record in records:
            param_list = record.get('param_name_list', [])
            if isinstance(param_list, list):
                scanned_params.update(param_list)
        
        return scanned_params
    
    def add_scanned_param(self, url_path, param_name, website=None):
        """
        添加已扫描的参数记录
        
        Args:
            url_path: str - URL路径（带泛化，如：http://127.0.0.1/{string-7}）
            param_name: str/list - 参数名或参数名列表
            website: str - 站点URL（可选）
        
        Returns:
            bool - 是否添加成功
        """
        if not self.collection_name:
            print(f"[VulnParamDatabase] collection_name 为空，无法写入")
            return False
        
        print(f"[VulnParamDatabase] 开始写入: collection={self.collection_name}, url_path={url_path}, params={param_name}, website={website}")
        
        try:
            # 处理参数名（支持单个或列表）
            param_list = param_name if isinstance(param_name, list) else [param_name]
            
            # 先查询是否已存在该url_path的记录
            query = {'url_path': url_path}
            if website:
                query['website'] = website
            
            existing = self.db_handler.find_one(self.collection_name, query)
            
            if existing:
                # 已存在，更新参数列表（追加新参数）
                existing_params = set(existing.get('param_name_list', []))
                existing_params.update(param_list)
                
                # 更新记录
                update_data = {
                    'param_name_list': list(existing_params),
                    'time': self.Core_Function.callback_time(0)
                }
                
                self.db_handler.update_one(
                    self.collection_name,
                    {'_id': existing['_id']},
                    update_data
                )
                print(f"[VulnParamDatabase] 更新成功: {len(existing_params)} 个参数")
            else:
                # 不存在，创建新记录
                record = {
                    'website': website,
                    'url_path': url_path,
                    'param_name_list': param_list,
                    'time': self.Core_Function.callback_time(0)
                }
                
                self.db_handler.insert_one(self.collection_name, record)
                print(f"[VulnParamDatabase] 插入成功: {len(param_list)} 个参数")
            
            return True
        except Exception as e:
            print(f"[VulnParamDatabase] 写入失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def batch_add_scanned_params(self, url_path, param_names, website=None):
        """
        批量添加已扫描的参数
        
        Args:
            url_path: str - URL路径（已标准化）
            param_names: list - 参数名列表
            website: str - 站点URL（可选）
        
        Returns:
            bool - 是否添加成功
        """
        return self.add_scanned_param(url_path, param_names, website)
    
    def delete_all_params(self):
        """
        删除所有已扫描参数记录
        
        Returns:
            int - 删除的记录数量
        """
        if not self.collection_name:
            return 0
        result = self.db_handler.delete_many(self.collection_name, {})
        if result:
            return result.deleted_count
        return 0
    
    def count_params(self):
        """获取已扫描参数记录总数"""
        if not self.collection_name:
            return 0
        return self.db_handler.count_documents(self.collection_name, {})
