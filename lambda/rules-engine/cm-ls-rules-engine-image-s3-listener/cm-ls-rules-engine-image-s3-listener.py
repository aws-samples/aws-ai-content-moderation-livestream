import json
import boto3
import os

IMAGE_PROCESSOR_WORKFLOW_ARN = os.environ["IMAGE_PROCESSOR_WORKFLOW_ARN"]
stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    if event is None or "Records" not in event or len(event["Records"]) == 0:
         return {
            'statusCode': 400,
            'body': 'Invalid trigger'
        }
    s3_bucket, s3_key, channel_id, file_name = None, None, None, None
    try:
        s3_bucket = event["Records"][0]["s3"]["bucket"]["name"]
        s3_key = event["Records"][0]["s3"]["object"]["key"]
        
        channel_id = s3_key.split('/')[3]
        file_name = s3_key.split('/')[-1]

    except ex as Exception:
        print(ex)
        return {
            'statusCode': 400,
            'body': f'Error parsing S3 trigger: {ex}'
        }
        
    result = {
            's3_bucket': s3_bucket,
            's3_key': s3_key,
            'channel_id': channel_id,
        }
        
    # invoke step function state machine
    response = stepfunctions.start_execution(
        stateMachineArn=IMAGE_PROCESSOR_WORKFLOW_ARN,
        input=json.dumps(result)
    )
    
    return {
        'statusCode': 200,
        'body': result
    }
