import json
import boto3
import time, datetime
import os

DYNAMO_WARNING_TABLE = os.environ["DYNAMO_WARNING_TABLE"]
DYNAMO_CACHE_TABLE = os.environ["DYNAMO_CACHE_TABLE"]

ACK_SLA_S = int(os.environ["ACK_SLA_S"]) # Acknowledge SLA in second, set "serverity" to 'WARN' if exceeded SLA (timestamp - now) > ACK_SLA_S
S3_PRE_SIGNED_URL_EXPIRY_S = os.environ["S3_PRE_SIGNED_URL_EXPIRY_S"] # 1 hour

dynamodb_res = boto3.resource('dynamodb')
warning_table =  dynamodb_res.Table(DYNAMO_WARNING_TABLE)
cache_table =  dynamodb_res.Table(DYNAMO_CACHE_TABLE)
ivs = boto3.client('ivs')
s3 = boto3.client('s3')


def lambda_handler(event, context):

    s_response = ivs.list_streams()
    d_response = warning_table.scan(
            FilterExpression="#status >= :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "CREATED"} 
        )
    
    account_id = context.invoked_function_arn.split(":")[4]
    
    streams = s_response.get("streams", [])
    warnings = d_response.get('Items', [])
        
    now = int(time.time()) # Epoch
    result = []
    for s in streams:
        channel_arn = s["channelArn"]
        channel_id = channel_arn.split('/')[-1]

        r = {
            "channel_id": channel_id,
            "stream": {
                "channel_arn": channel_arn, 
                "health": s["health"],
                "start_time": s["startTime"].timestamp(), #Epoch time
                "state": s["state"],
                "stream_id": s["streamId"],
                "view_count": s["viewerCount"]
            },
            "warnings": []
        }   
        
        try:
            # Get lastest screenshot from cache
            cache = get_cache(channel_id)
            if cache is not None:
                thumbnail_bucket = cache["image"].get("image_s3_bucket")
                thumbnail_key = cache["image"].get("image_s3_key")

                if thumbnail_bucket is not None and thumbnail_key is not None:
                    r["image_url"] = s3.generate_presigned_url(
                            'get_object', 
                            Params={
                                'Bucket': thumbnail_bucket, 
                                'Key': thumbnail_key
                            }, ExpiresIn=S3_PRE_SIGNED_URL_EXPIRY_S)
                    print(r["image_url"])
        except Exception as ex:
            print(ex)
        
        # Get channel information
        c_response = ivs.get_channel(arn=channel_arn)
        if c_response is not None and 'channel' in c_response:
            r["channel"] = c_response["channel"]

        for w in warnings:
            if w["channel_id"] == channel_id and w["status"] == "CREATED":
                w["image"]["url"] = s3.generate_presigned_url(
                    'get_object', 
                    Params={
                        'Bucket': w["image"]["bucket"], 
                        'Key': w["image"]["key"]
                    }, ExpiresIn=S3_PRE_SIGNED_URL_EXPIRY_S)
                if now - float(w["timestamp"]) > ACK_SLA_S:
                    w["severity"] = "HIGH"
                else:
                    w["severity"] = "MEDIUM"
                r["warnings"].append(w)
        
        result.append(r)
            
        
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }

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