import logging
from .database import get_mongo_client, MONGO_DATABASE

logger = logging.getLogger(__name__)

def get_adunit_by_uuid(uuid):
    """根據 UUID 從 MongoDB 取得 AdUnit 資料"""
    try:
        client = get_mongo_client()
        if not client:
            return None
            
        db = client[MONGO_DATABASE]
        collection = db['AdUnit']
        
        # 查詢 AdUnit
        adunit = collection.find_one({"uuid": uuid})
        return adunit
        
    except Exception as e:
        logger.error(f"查詢 AdUnit 時發生錯誤: {str(e)}")
        return None
    finally:
        if client:
            client.close() 