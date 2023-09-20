import json
import boto3
import os

DYNAMO_CONFIG_TABLE = os.environ["DYNAMO_CONFIG_TABLE"]
DYNAMO_CACHE_TABLE = os.environ["DYNAMO_CACHE_TABLE"]

dynamodb_res = boto3.resource('dynamodb')
config_table =  dynamodb_res.Table(DYNAMO_CONFIG_TABLE)
cache_table =  dynamodb_res.Table(DYNAMO_CACHE_TABLE)

def lambda_handler(event, context):
    config = event.get("config", None)
    if config is None:
        return {
            'statusCode': 400,
            'body': 'Config is required.'
        }
    
    # Update DynamoDB  
    c_response = config_table.put_item(Item=config)

    # Cleanup cache
    # Scan the table to retrieve all items
    response = cache_table.scan()
    
    # Delete each item
    for item in response.get('Items', []):
        cache_table.delete_item(
            Key={
                'channel_id': item['channel_id']
            }
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Config updated.')
    }
