'''
Content Moderation Live Stream Monitor Service: Listener
Subscribe to the Rules Egine SNS top receiving moderation warnings

status: "CREATED", "ACKED", "RESOLVED"
action: "marked as fp", "stream terminated"
'''
import json
import boto3
import os

DYNAMO_WARNING_TABLE = os.environ["DYNAMO_WARNING_TABLE"]

dynamodb_res = boto3.resource('dynamodb')
warning_table =  dynamodb_res.Table(DYNAMO_WARNING_TABLE)

def lambda_handler(event, context):
    #print(event)
    if event is None or "Records" not in event or len(event["Records"]) == 0:
        msg = f'Invalid trigger: {json.dumps(event)}'
        print(msg)
        return {
            'statusCode': 400,
            'body': msg
        }        
    
    for r in event["Records"]:
        try:
            m = json.loads(r["Sns"]["Message"])
            m = m["moderation_result"]

            # Store to DB
            result = []
            for r in m["result"]:
                result.append(
                    {
                        "rule": {
                            "categories": r["rule"]["categories"],
                            "confidence_threshold": str(r["rule"]["confidence_threshold"])
                        },
                        "moderation": {
                            "Confidence": str(r["moderation"]["Confidence"]),
                            "Name": r["moderation"]["Name"],
                            "ParentName": r["moderation"]["ParentName"],
                        },
                        "description": r["description"]
                    }
                )
            
            response = warning_table.put_item(Item={
                "id": f'{m["channel_id"]}_{m["timestamp"]}',
                "channel_id": m["channel_id"],
                "timestamp": m["timestamp"],
                "result": result,
                "image": m["image"],
                "status": 'CREATED'
            })
            
        except Exception as ex:
            msg = f'Failed to parse moderation message: {ex}'
            raise ex
            print(msg)
            return {
                'statusCode': 400,
                'body': msg
            }   
        
    return {
        'statusCode': 200,
        'body': 'Warning received'
    }
