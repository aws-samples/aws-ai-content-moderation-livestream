import json
import boto3
import time
import os

DYNAMO_WARNING_TABLE = os.environ["DYNAMO_WARNING_TABLE"]

ivs = boto3.client('ivs')
dynamodb_res = boto3.resource('dynamodb')
warning_table =  dynamodb_res.Table(DYNAMO_WARNING_TABLE)

SUPPORTED_ACTIONS = ["stopstream", "dismisswarning"]

def lambda_handler(event, context):
    channel_arn = event.get("channel_arn")
    if channel_arn is None or len(channel_arn) == 0:
        return {
            'statusCode': 400,
            'body': 'Channel ARN required to stop a stream.'
        }
    action = event.get("action")
    if action is None or len(action) == 0 or action.lower() not in SUPPORTED_ACTIONS:
        return {
            'statusCode': 400,
            'body': f'Acknowledge warning requires action. Supported values: {", ".join(SUPPORTED_ACTIONS)}'
        }
    channel_id = channel_arn.split('/')[-1]

    if action == "stopstream":
        response = ivs.stop_stream(
            channelArn=channel_arn
        )
    
    # Update warning status
    # get all the warnings for the given channel
    warnings = []
    if channel_id is not None and len(channel_id) > 0:
        d_response = warning_table.scan(
            FilterExpression="#channel_id >= :channel_id",
            ExpressionAttributeNames={"#channel_id": "channel_id"},
            ExpressionAttributeValues={":channel_id": channel_id} 
        )
        warnings = d_response.get('Items', [])
    
    # update warning status
    for w in warnings:
        if w["status"] != "CREATED":
            continue
        
        if action == "stopstream":
            w["status"] = "STOPPED"
        elif action == "dismisswarning":
            w["status"] = "DISMISSED"
        
        w["ack_timestamp"] = int(time.time()) # Epoch
        warning_table.put_item(Item=w)

    return {
        'statusCode': 200,
        'body': json.dumps('Acknowledged the warning(s)')
    }
