'''
1. Get config: channel level and global level
2. Get cache
3. Check if frequency allowed
'''
import json
import boto3
import time
from boto3.dynamodb.conditions import Attr
import re
import os

DYNAMO_CONFIG_TABLE = os.environ["DYNAMO_CONFIG_TABLE"]
DYNAMO_CACHE_TABLE = os.environ["DYNAMO_CACHE_TABLE"]

LOCAL_TEMP_PATH = '/tmp/'
IVS_CHANNEL_ARN_TEMPLATE = 'arn:aws:ivs:{REGION}:{ACCOUNT_ID}:channel/{channel_id}'

s3 = boto3.client('s3')
ivs = boto3.client('ivs')

dynamodb_res = boto3.resource('dynamodb')
config_table =  dynamodb_res.Table(DYNAMO_CONFIG_TABLE)
cache_table =  dynamodb_res.Table(DYNAMO_CACHE_TABLE)

def lambda_handler(event, context):
    if event is None:
         return {
            'status_code': 400,
            'message': 'Invalid input'
        }
    
    s3_bucket = event.get("s3_bucket")
    s3_key = event.get("s3_key")
    
    account_id = context.invoked_function_arn.split(":")[4]
    region = context.invoked_function_arn.split(":")[3]
    
    channel_id = event.get("channel_id")
    channel_arn = IVS_CHANNEL_ARN_TEMPLATE.replace("{REGION}",region).replace("{ACCOUNT_ID}", account_id).replace("{channel_id}", channel_id)
    if s3_bucket is None or s3_key is None or channel_id is None:
        msg = f'Invalid input: {json.dumps(event)}'
        print(msg)
        return {
            'status_code': 400,
            'message': msg
        }
    
    file_name = s3_key.split('/')[-1]
        
    # Validate file extension
    if file_name.split('.')[-1].lower() not in ["jpg","jpeg","png"]: 
        msg = f'Not supported image type: {file_name}'
        print(msg)
        return {
            'status_code': 400,
            'message': msg
        }
        
    # Get Config from DynamoDB
    config = get_config(channel_id, channel_arn)
    print("### 1.1 Get config", config)
    if config is None:
        msg = f'Config not found. Channel Id: {channel_id}'
        print(msg)
        return {
            'status_code': 400,
            'message': msg
        }
    # Get channel cache: from Redis or DynamoDB
    cache = get_cache(channel_id)
    print("### 1.2 Get cache", cache)

    now = int(time.time()) # Epoch
    # Check Frequency
    print(f'### 2 check moderation frequency.')
    if "last_ts" in cache["image"] and cache["image"]["last_ts"] is not None:
        if now - cache["image"]["last_ts"] < config["image"]["sample_frequency_s"]:
            msg = f'Less than {config["image"]["sample_frequency_s"]} seconds from previous sample. Current ts: {now}, last ts: {cache["image"].get("last_ts")}, delta: {now-cache["image"].get("last_ts")}, threshold: {config["image"]["sample_frequency_s"]}'
            print("!!! exit", msg)
            return {
                'status_code': 400,
                'message': msg
            }
    # update cache with ts
    update_cache(cache, now, image_s3_bucket=s3_bucket, image_s3_key=s3_key)
    
    return {
        'status_code': 200,
        'message': f'Frequency threshold exceeded. Proceed to the next step.',
        'config': config,
        'cache': cache,
        'ignore_similar': config["image"]["ignore_similar"],
        'timestamp': now,
        's3_bucket': s3_bucket,
        's3_key': s3_key,
        'channel_id': channel_id,
        "channel_arn": channel_arn
    }

def get_config(channel_id, channel_arn):
    config_response = config_table.query(
        KeyConditionExpression="channel_id = :channel_id",
        ExpressionAttributeValues={":channel_id": channel_id}
    )
    print("### 1.0.1 Get channel config", config_response)
    if "Items" in config_response and len(config_response["Items"]) > 0:
        return config_response["Items"][0]
    else:
        # No config for the channel Id, find global config with regex matching channel name
        
        # Get channel name
        channel_name = None
        try:
            c_response = ivs.get_channel(arn=channel_arn)
            if c_response is not None and 'channel' in c_response:
                channel_name = c_response["channel"]["name"]
            print("### 1.0.2 No Channel config. Get channel name", channel_name)
        except Exception as ex:
            print(ex)

        if channel_name is None or len(channel_name) == 0:
            return None
        
        # Get global configs
        config_response = config_table.scan(
            FilterExpression=Attr('global_flag').eq(True)
        )
        print("### 1.0.3 Get Global configs", config_response)
        if "Items" in config_response:
            final_config = None
            for config in config_response["Items"]:
                print("### 1.0.4 Match Global configs regex", config["channel_name_regex"], re.search(config["channel_name_regex"], channel_name))
                if config["channel_name_regex"] is not None and len(config["channel_name_regex"]) > 0 \
                        and re.search(config["channel_name_regex"], channel_name):
                    if final_config is None or final_config["priority"] is None or final_config["priority"] > config['priority']:
                        final_config = config
            print("### 1.0.5 Get Global config", final_config)
            return final_config
            
    return None
    
def get_cache(channel_id):
    cache = None
    response = cache_table.query(
        KeyConditionExpression="channel_id = :channel_id",
        ExpressionAttributeValues={":channel_id": channel_id}
    )
    if "Items" in response and len(response["Items"]) > 0:
        cache = response["Items"][0]
    else:
        cache = {
            "channel_id": channel_id,
            "image": {
                "last_ts": None, # epoch
                "last_image_hash": None
            }
        }
    return cache

def update_cache(cache, timestamp=None, image_hash=None, image_s3_bucket=None, image_s3_key=None):
    try:
        if timestamp is not None:
            cache["image"]["last_ts"] = timestamp
        if image_hash is not None:
            cache["image"]["last_image_hash"] =str(image_hash)
        if image_s3_bucket is not None:
            cache["image"]["image_s3_bucket"] = image_s3_bucket
        if image_s3_key is not None:
            cache["image"]["image_s3_key"] = image_s3_key
            
        response = cache_table.put_item(Item=cache)
    except Exception as e:
        print("Failed to update cache to DynamoDB:", e)
