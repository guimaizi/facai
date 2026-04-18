from .mongodb_handler import MongoDBHandler
import time

class ProjectDatabase:
    def __init__(self):
        self.db_handler = MongoDBHandler()
        self.collection = self.db_handler.get_collection('project_config')

    def get_all_projects(self):
        """获取所有项目"""
        projects = self.db_handler.find('project_config', {})
        # 转换ObjectId为字符串，便于JSON序列化
        result = []
        for project in projects:
            if '_id' in project:
                project['_id'] = str(project['_id'])
            result.append(project)
        return result

    def get_project_by_name(self, project_name):
        """根据项目名称获取项目"""
        project = self.db_handler.find_one('project_config', {'Project': project_name})
        if project and '_id' in project:
            project['_id'] = str(project['_id'])
        return project

    def add_project(self, project_data):
        """添加项目"""
        project_data['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        project_data['status_code'] = 0  # 默认未运行
        return self.db_handler.insert_one('project_config', project_data)

    def update_project(self, project_name, project_data):
        """更新项目"""
        return self.db_handler.update_one('project_config', {'Project': project_name}, project_data)

    def delete_project(self, project_name):
        """删除项目"""
        return self.db_handler.delete_one('project_config', {'Project': project_name})

    def get_running_project(self):
        """获取运行中的项目"""
        project = self.db_handler.find_one('project_config', {'status_code': 1})
        if project and '_id' in project:
            project['_id'] = str(project['_id'])
        return project

    def start_project(self, project_name):
        """启动项目"""
        # 先停止所有运行中的项目
        self.db_handler.update_one('project_config', {'status_code': 1}, {'status_code': 0})
        # 启动指定项目
        return self.db_handler.update_one('project_config', {'Project': project_name}, {'status_code': 1})

    def stop_project(self, project_name):
        """停止项目"""
        return self.db_handler.update_one('project_config', {'Project': project_name}, {'status_code': 0})

    def get_project_count(self):
        """获取项目总数"""
        return self.db_handler.count_documents('project_config')

    def get_project_status(self, project_name):
        """获取项目状态"""
        project = self.get_project_by_name(project_name)
        if project:
            return project.get('status_code', 0)
        return 0

    def get_service_lock(self, project_name):
        """获取项目的服务锁状态"""
        project = self.get_project_by_name(project_name)
        if project:
            return project.get('service_lock', {
                'spider_service': 0,
                'monitor_service': 0,
                'scaner_service': 0
            })
        return {
            'spider_service': 0,
            'monitor_service': 0,
            'scaner_service': 0
        }

    def update_service_lock(self, project_name, service_name, status):
        """
        更新项目的服务锁状态
        
        Args:
            project_name: 项目名称
            service_name: 服务名称 (spider_service/monitor_service/scaner_service)
            status: 状态 (0/1)
        
        Returns:
            bool: 更新是否成功
        """
        # 获取当前服务锁状态
        service_lock = self.get_service_lock(project_name)
        print(f"[DEBUG] Current service_lock for {project_name}: {service_lock}")
        print(f"[DEBUG] Updating {service_name} to {status}")
        
        # 互斥检查：spider_service 和 monitor_service 不能同时为1
        if status == 1:
            if service_name == 'spider_service':
                # 开启爬虫服务时，关闭资产监控
                service_lock['monitor_service'] = 0
                print(f"[DEBUG] Mutex: closing monitor_service")
            elif service_name == 'monitor_service':
                # 开启资产监控时，关闭爬虫服务
                service_lock['spider_service'] = 0
                print(f"[DEBUG] Mutex: closing spider_service")
        
        # 更新目标服务状态
        service_lock[service_name] = status
        print(f"[DEBUG] New service_lock: {service_lock}")
        
        # 保存到数据库
        result = self.db_handler.update_one(
            'project_config',
            {'Project': project_name},
            {'service_lock': service_lock}
        )
        print(f"[DEBUG] Update result: {result}")
        return result