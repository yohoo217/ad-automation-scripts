import logging
from .database import get_mongo_client, MONGO_DATABASE

logger = logging.getLogger(__name__)

def get_adunit_by_uuid(uuid):
    """Get AdUnit data from MongoDB by UUID"""
    try:
        client = get_mongo_client()
        if not client:
            return None

        db = client[MONGO_DATABASE]
        collection = db['AdUnit']

        # Query AdUnit
        adunit = collection.find_one({"uuid": uuid})
        return adunit

    except Exception as e:
        logger.error(f"Error querying AdUnit: {str(e)}")
        return None
    finally:
        if client:
            client.close()
