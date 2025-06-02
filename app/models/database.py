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

def get_camp_id_by_adset_id(adset_id):
    """根據 AdSet ID 查找對應的 Campaign ID"""
    try:
        client = get_mongo_client()
        if not client:
            logger.error("無法連接到 MongoDB")
            return None
            
        db = client[MONGO_DATABASE]
        adset_collection = db.AdSet
        
        # 查找 AdSet 文檔
        adset_doc = adset_collection.find_one({"uuid": adset_id})
        
        if adset_doc and "campId" in adset_doc:
            logger.info(f"找到 AdSet {adset_id} 對應的 campId: {adset_doc['campId']}")
            return adset_doc["campId"]
        else:
            logger.warning(f"找不到 AdSet ID: {adset_id} 或該 AdSet 沒有 campId")
            return None
            
    except Exception as e:
        logger.error(f"查找 campId 時發生錯誤: {str(e)}")
        return None
    finally:
        if 'client' in locals():
            client.close()

def get_campaign_name_by_camp_id(camp_id):
    """根據 Campaign ID 查找活動名稱"""
    try:
        client = get_mongo_client()
        if not client:
            logger.error("無法連接到 MongoDB")
            return None
            
        db = client[MONGO_DATABASE]
        campaign_collection = db.Campaign
        
        # 查找 Campaign 文檔
        campaign_doc = campaign_collection.find_one({"uuid": camp_id})
        
        if campaign_doc and "name" in campaign_doc:
            logger.info(f"找到 Campaign {camp_id} 的名稱: {campaign_doc['name']}")
            return campaign_doc["name"]
        else:
            logger.warning(f"找不到 Campaign ID: {camp_id} 或該 Campaign 沒有 name")
            return None
            
    except Exception as e:
        logger.error(f"查找 Campaign 名稱時發生錯誤: {str(e)}")
        return None
    finally:
        if 'client' in locals():
            client.close()

def get_activity_name_by_adset_id(adset_id):
    """根據 AdSet ID 查找活動名稱（整合查詢）"""
    try:
        # 第一步：根據 AdSet ID 查找 Campaign ID
        camp_id = get_camp_id_by_adset_id(adset_id)
        if not camp_id:
            logger.warning(f"無法找到 AdSet {adset_id} 對應的 Campaign ID")
            return None
            
        # 第二步：根據 Campaign ID 查找活動名稱
        campaign_name = get_campaign_name_by_camp_id(camp_id)
        if not campaign_name:
            logger.warning(f"無法找到 Campaign {camp_id} 的名稱")
            return None
            
        logger.info(f"成功查找到 AdSet {adset_id} 對應的活動名稱: {campaign_name}")
        return campaign_name
        
    except Exception as e:
        logger.error(f"查找活動名稱時發生錯誤: {str(e)}")
        return None 