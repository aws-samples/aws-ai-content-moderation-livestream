'''
Get all the channels with streams and latest thumbnail
'''
import json
import boto3
import time, datetime
from decimal import *

dynamodb_res = boto3.resource('dynamodb')
config_table =  dynamodb_res.Table('cm-livestream-config')
ivs = boto3.client('ivs')
s3 = boto3.client('s3')

S3_PRE_SIGNED_URL_EXPIRY_S = 3600 # 1 hour

AWS_ACCOUNT_ID = '122702569249'
IVS_THUMBNAIL_S3_BUCKET = 'wwso-cm-livestream-demo'
IVS_THUMBNAIL_PREFIX = "ivs/v1/" # Template: "ivs/v1/{account_id}/{channel_id}/{year}/{month}/{day}/{hour}/{minute}/{recording_id}"
 
def lambda_handler(event, context):

    include_stream = event.get("include_stream", False)
    include_thumbnail = event.get("include_thumbnail", False)
    include_config = event.get("include_config", False)
    
    result = []
    channels, streams, configs = [], [], []

    c_response = ivs.list_channels()
    channels = c_response.get('channels', [])
    
    if include_stream:
        s_response = ivs.list_streams()
        streams = s_response.get("streams", [])
        
    if include_config:
        config_response = config_table.scan()
        configs = config_response["Items"]

    for c in channels:    
        arn = c["arn"]
        c["id"] = arn.split('/')[-1]
        if include_stream:
            for s in streams:
                if s["channelArn"] == arn:
                    c["stream"] = {
                        "channel_arn": arn, 
                        "health": s["health"],
                        "start_time": s["startTime"].timestamp(), #Epoch time
                        "state": s["state"],
                        "stream_id": s["streamId"],
                        "view_count": s["viewerCount"]
                    }
                    break
        if include_thumbnail:
            try:
                # Get lastest screenshot
                dt_now = datetime.datetime.now()
                c["image_url"] = get_lastest_thumbnail(IVS_THUMBNAIL_S3_BUCKET, f'{IVS_THUMBNAIL_PREFIX}{AWS_ACCOUNT_ID}/{arn.split("/")[-1]}/')
            except Exception as ex:
                print(ex)
                
        if include_config:
            for config in configs:
                if config["channel_id"] == c["id"]:
                    c["config"] = convert_to_json_with_floats(config)
                    break
        
        result.append(c)

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }

def convert_to_json_with_floats(data):
    def default_converter(o):
        if isinstance(o, Decimal):
            return float(o)
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")
    
    json_data = json.dumps(data, default=default_converter)
    return json.loads(json_data)
    
def get_lastest_thumbnail(s3_bucket, s3_prefix):
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_prefix)

    jpg_png_files = []
    
    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('.jpg') or key.endswith('.png'):
                jpg_png_files.append((key, obj['LastModified']))
    
    # Find the latest file
    if len(jpg_png_files) > 0:
        latest_file = max(jpg_png_files, key=lambda item: item[1])
        if len(latest_file) > 0:
            return s3.generate_presigned_url(
                    'get_object', 
                    Params={
                        'Bucket': s3_bucket, 
                        'Key': latest_file[0]
                    }, ExpiresIn=S3_PRE_SIGNED_URL_EXPIRY_S)
    return None
