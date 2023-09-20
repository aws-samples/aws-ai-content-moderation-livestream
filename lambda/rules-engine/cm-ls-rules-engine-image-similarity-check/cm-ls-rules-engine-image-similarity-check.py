import json
import boto3
import time
from PIL import Image
import imagehash
from boto3.dynamodb.conditions import Attr
import re
from io import BytesIO
import os


DYNAMO_CACHE_TABLE = os.environ["DYNAMO_CACHE_TABLE"]
LOCAL_TEMP_PATH = '/tmp/'

s3 = boto3.client('s3')

dynamodb_res = boto3.resource('dynamodb')
cache_table =  dynamodb_res.Table(DYNAMO_CACHE_TABLE)


def lambda_handler(event, context):
    if event is None or event.get("status_code") != 200:
        return {
            'status_code': 400,
            'message': 'Invalid input'
        }
    
    config = event.get("config", None)
    cache = event.get("cache", None)
    timestamp = event.get("timestamp", None)
    
    s3_bucket = event.get("s3_bucket")
    s3_key = event.get("s3_key")
    channel_id = event.get("channel_id")
    
    if config is None or cache is None or s3_bucket is None or s3_key is None:
        return {
            'status_code': 400,
            'message': 'Invalid input'
        }
 
    file_name = s3_key.split('/')[-1]

    # Check similarity
    if "image" in config and config["image"]["ignore_similar"] == True:
        print(f"### 3 check image similarity.")
        
        # Read image bytes
        s3_response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        image_data = s3_response['Body'].read()
        image = Image.open(BytesIO(image_data))
        
        # Get current image phash
        current_hash = imagehash.phash(image)
        
        if "last_image_hash" not in cache["image"] or cache["image"]["last_image_hash"] is None:
            print(f"### 3.1 no previous image cache. Ignore comparision")
            update_cache(cache, timestamp, str(current_hash))

        else:
            # Load previous hash
            prev_hash = imagehash.hex_to_hash(cache["image"]["last_image_hash"])

            print(f'### 3.2 compare similarity with the previous image. Diff: {abs(prev_hash - current_hash)}, threshold: {config["image"]["image_hash_threshold"]}')
            if abs(prev_hash - current_hash) <= config["image"]["image_hash_threshold"]:
                update_cache(cache, timestamp, str(current_hash))
                msg = f'Ignore similiar image. Diff: {abs(prev_hash - current_hash)}, threshold: {config["image"]["image_hash_threshold"]}'
                print("!!! exit", msg)
                return {
                    'status_code': 400,
                    'message': msg
                }
            else:
                # update cache with latest hash
                update_cache(cache, timestamp, str(current_hash))
    else:
        return event

    event["message"] = 'Not a similar image. Proceed to the next step.'
    return event

def update_cache(cache, timestamp=None, image_hash=None):
    try:
        if timestamp is not None:
            cache["image"]["last_ts"] = timestamp
        if image_hash is not None:
            cache["image"]["last_image_hash"] =str(image_hash)

            
        response = cache_table.put_item(Item=cache)
    except Exception as e:
        print("Failed to update cache to DynamoDB:", e)