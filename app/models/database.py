import os
import logging
from pymongo import MongoClient
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# MongoDB configuration
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'ad_database')

def get_mongo_client():
    """Get MongoDB connection"""
    try:
        if MONGO_CONNECTION_STRING:
            client = MongoClient(MONGO_CONNECTION_STRING)
            return client
        else:
            # Backup connection method (if environment variable doesn't exist)
            username = os.getenv('MONGO_USERNAME', 'mongodb_user')
            password = os.getenv('MONGO_PASSWORD', 'your_password_here')
            hosts = "localhost:27017"  # Modify to your MongoDB host address
            database = MONGO_DATABASE

            connection_string = f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{hosts}/{database}?replicaSet=rs0&authMechanism=SCRAM-SHA-1"
            client = MongoClient(connection_string)
            return client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return None

def get_camp_id_by_adset_id(adset_id):
    """Find corresponding Campaign ID by AdSet ID"""
    try:
        client = get_mongo_client()
        if not client:
            logger.error("Unable to connect to MongoDB")
            return None

        db = client[MONGO_DATABASE]
        adset_collection = db.AdSet

        # Find AdSet document
        adset_doc = adset_collection.find_one({"uuid": adset_id})

        if adset_doc and "campId" in adset_doc:
            logger.info(f"Found AdSet {adset_id} corresponding campId: {adset_doc['campId']}")
            return adset_doc["campId"]
        else:
            logger.warning(f"Cannot find AdSet ID: {adset_id} or this AdSet has no campId")
            return None

    except Exception as e:
        logger.error(f"Error finding campId: {str(e)}")
        return None
    finally:
        if 'client' in locals():
            client.close()

def get_campaign_name_by_camp_id(camp_id):
    """Find campaign name by Campaign ID"""
    try:
        client = get_mongo_client()
        if not client:
            logger.error("Unable to connect to MongoDB")
            return None

        db = client[MONGO_DATABASE]
        campaign_collection = db.Campaign

        # Find Campaign document
        campaign_doc = campaign_collection.find_one({"uuid": camp_id})

        if campaign_doc and "name" in campaign_doc:
            logger.info(f"Found Campaign {camp_id} name: {campaign_doc['name']}")
            return campaign_doc["name"]
        else:
            logger.warning(f"Cannot find Campaign ID: {camp_id} or this Campaign has no name")
            return None

    except Exception as e:
        logger.error(f"Error finding Campaign name: {str(e)}")
        return None
    finally:
        if 'client' in locals():
            client.close()

def get_activity_name_by_adset_id(adset_id):
    """Find activity name by AdSet ID (integrated query)"""
    try:
        # Step 1: Find Campaign ID by AdSet ID
        camp_id = get_camp_id_by_adset_id(adset_id)
        if not camp_id:
            logger.warning(f"Unable to find Campaign ID corresponding to AdSet {adset_id}")
            return None

        # Step 2: Find activity name by Campaign ID
        campaign_name = get_campaign_name_by_camp_id(camp_id)
        if not campaign_name:
            logger.warning(f"Unable to find name for Campaign {camp_id}")
            return None

        logger.info(f"Successfully found activity name for AdSet {adset_id}: {campaign_name}")
        return campaign_name

    except Exception as e:
        logger.error(f"Error finding activity name: {str(e)}")
        return None
