import os
import logging
from pymongo import MongoClient
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# MongoDB 配置
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'trek')

def get_mongo_client():
    """取得 MongoDB 連接"""
    try:
        if MONGO_CONNECTION_STRING:
            client = MongoClient(MONGO_CONNECTION_STRING)
            return client
        else:
            # 備用連線方式（如果環境變數不存在）
            username = os.getenv('MONGO_USERNAME', 'trekread')
            password = os.getenv('MONGO_PASSWORD', 'HNwMUr0NCKZejRMzxLbAWOnRYIrPT9qZuzL0')
            hosts = "172.105.200.150:27017,139.162.91.194:27017,172.105.208.153:27017"
            database = MONGO_DATABASE
            
            connection_string = f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{hosts}/{database}?replicaSet=rs0&authMechanism=SCRAM-SHA-1"
            client = MongoClient(connection_string)
            return client
    except Exception as e:
        logger.error(f"MongoDB 連接失敗: {str(e)}")
        return None 