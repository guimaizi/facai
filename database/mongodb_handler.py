import pymongo
import json
import os

class MongoDBHandler:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.client = None
        self.db = None
        self.connect()

    def load_config(self, config_file):
        # 使用Class_Core_Function中的callback_config方法加载配置
        try:
            from service.Class_Core_Function import Class_Core_Function
            core_function = Class_Core_Function()
            config = core_function.callback_config()
            mongodb_config = config.get('mongodb', {}) if config else {}
            if mongodb_config:
                return mongodb_config
        except Exception as e:
            print(f"使用callback_config加载配置失败: {e}")

        #  fallback to original method
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('mongodb', {})
        return {
            'ip': '127.0.0.1',
            'port': 27017,
            'dbname': 'facai',
            'username': '',
            'password': ''
        }

    def connect(self):
        try:
            if self.config.get('username') and self.config.get('password'):
                uri = f"mongodb://{self.config['username']}:{self.config['password']}@{self.config['ip']}:{self.config['port']}/"
            else:
                uri = f"mongodb://{self.config['ip']}:{self.config['port']}/"
            
            self.client = pymongo.MongoClient(uri)
            self.db = self.client[self.config['dbname']]
            return True
        except Exception as e:
            print(f"MongoDB连接失败: {e}")
            return False

    def get_collection(self, collection_name):
        if self.db is not None:
            return self.db[collection_name]
        return None

    def insert_one(self, collection_name, data):
        collection = self.get_collection(collection_name)
        if collection is not None:
            return collection.insert_one(data)
        return None

    def find(self, collection_name, query=None, projection=None, limit=None, sort=None, skip=None):
        collection = self.get_collection(collection_name)
        if collection is not None:
            cursor = collection.find(query, projection)
            if sort:
                cursor = cursor.sort(sort)
            if skip is not None:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        return []

    def find_one(self, collection_name, query=None, projection=None):
        collection = self.get_collection(collection_name)
        if collection is not None:
            return collection.find_one(query, projection)
        return None

    def update_one(self, collection_name, query, update_data):
        collection = self.get_collection(collection_name)
        if collection is not None:
            try:
                result = collection.update_one(query, {'$set': update_data})
                print(f"[MongoDB] update_one - matched_count: {result.matched_count}, modified_count: {result.modified_count}")
                print(f"[MongoDB] update_one - query: {query}")
                print(f"[MongoDB] update_one - update_data keys: {list(update_data.keys())}")
                if result.matched_count == 0:
                    print(f"[MongoDB] Warning: No document matched the query!")
                return result
            except Exception as e:
                print(f"[MongoDB] update_one error: {e}")
                print(f"[MongoDB] update_data: {update_data}")
                raise
        return None

    def update_many(self, collection_name, query, update_data):
        """批量更新多个文档"""
        collection = self.get_collection(collection_name)
        if collection is not None:
            return collection.update_many(query, {'$set': update_data})
        return None

    def delete_one(self, collection_name, query):
        collection = self.get_collection(collection_name)
        if collection is not None:
            return collection.delete_one(query)
        return None

    def delete_many(self, collection_name, query):
        collection = self.get_collection(collection_name)
        if collection is not None:
            return collection.delete_many(query)
        return None

    def count_documents(self, collection_name, query=None):
        collection = self.get_collection(collection_name)
        if collection is not None:
            return collection.count_documents(query or {})
        return 0

    def close(self):
        if self.client is not None:
            self.client.close()