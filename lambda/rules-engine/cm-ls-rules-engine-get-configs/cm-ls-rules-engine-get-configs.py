import json
import boto3
import re
from decimal import *
from boto3.dynamodb.conditions import Attr
import os

DYNAMO_CONFIG_TABLE = os.environ["DYNAMO_CONFIG_TABLE"]

dynamodb_res = boto3.resource('dynamodb')
config_table =  dynamodb_res.Table(DYNAMO_CONFIG_TABLE)

def lambda_handler(event, context):
    channel_id = event.get("channel_id")
    channel_name = event.get("channel_name")
    global_flag = event.get("global_flag")
    
    configs = []
    # Get config for the specific channel_id
    if channel_id is not None:
        configs = get_configs_by_channel_id(channel_id)

    # Get global configs based on channel_name (regx)
    if channel_name is not None:
        global_configs = get_global_configs(channel_name)
        configs = configs + global_configs
    
    # Get all configs
    if channel_id is None and channel_name is None:
        configs = get_all_configs()
        if global_flag is not None:
            result = []
            for c in configs:
                if global_flag == True and c.get("global_flag") == True:
                    result.append(c)
                elif global_flag == False and c.get("global_flag") == False:
                    result.append(c)
            configs = result      

    return {
        'statusCode': 200,
        'body': json.dumps(configs)
    }
    
def get_all_configs():
    configs = []
    
    config_response = config_table.scan()
    if config_response is not None and "Items" in config_response:
        configs = convert_to_json_with_floats(config_response["Items"]) 
    return configs
    
def get_configs_by_channel_id(channel_id):
    configs = []
    
    config_response = config_table.query(
        KeyConditionExpression="channel_id = :channel_id",
        ExpressionAttributeValues={":channel_id": channel_id}
    )
    if config_response is not None and "Items" in config_response:
        configs.append(convert_to_json_with_floats(config_response["Items"]))
        
    return configs
    
def get_global_configs(channel_name):
    configs = []
    
    # Get global configs
    response = config_table.scan(
        FilterExpression=Attr('global_flag').eq(True)
    )
    if response is not None and "Items" in response:
        for r in response["Items"]:
            if re.match(r["channel_name_regex"], channel_name):
                configs.append(convert_to_json_with_floats(r))
    
    return configs

def convert_to_json_with_floats(data):
    def default_converter(o):
        if isinstance(o, Decimal):
            return float(o)
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")
    
    json_data = json.dumps(data, default=default_converter)
    return json.loads(json_data)