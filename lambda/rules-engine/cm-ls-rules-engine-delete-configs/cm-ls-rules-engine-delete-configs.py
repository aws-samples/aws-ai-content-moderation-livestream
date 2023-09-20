import json
import boto3
import os

DYNAMO_CONFIG_TABLE = os.environ["DYNAMO_CONFIG_TABLE"]

dynamodb_res = boto3.resource('dynamodb')
config_table =  dynamodb_res.Table(DYNAMO_CONFIG_TABLE)

def lambda_handler(event, context):
    channel_ids = event.get("channel_ids", None)
    if channel_ids is None or len(channel_ids) == 0:
        return {
            'statusCode': 400,
            'body': 'channel_id is required.'
        }
    
    for channel_id in channel_ids:
        response = config_table.delete_item(
            Key={
                'channel_id': channel_id
            }
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Config deleted.')
    }
