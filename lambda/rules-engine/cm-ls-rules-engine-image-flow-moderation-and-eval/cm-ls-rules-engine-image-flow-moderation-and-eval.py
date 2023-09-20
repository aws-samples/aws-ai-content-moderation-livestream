import json
import boto3
import time

rekognition = boto3.client('rekognition')

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
 
    # Call Rek image moderation
    safe = True
    response = rekognition.detect_moderation_labels(
        Image={
           'S3Object': {
               'Bucket': s3_bucket,
               'Name': s3_key,
           }
        }
    )
    # Evaluate moderation rules
    mod_result = {
        "channel_id": channel_id,
        "timestamp": str(timestamp),
        "result": [],
        "image": {
                    "bucket": s3_bucket,
                    "key": s3_key
                }
    }
    print(f"### 4 Call rekognition moderation:", response)
    auto_stop = False
    if "ModerationLabels" in response and len(response["ModerationLabels"]) > 0 \
            and config is not None and "image" in config and config["image"]["rules"] is not None and len(config["image"]["rules"]) > 0:
        for d in response["ModerationLabels"]:
            for r in config["image"]["rules"]:
                # print(d, r)
                if (r["categories"] == ["*"] or d["Name"] in r["categories"]) and d["Confidence"] >= r["confidence_threshold"]:
                    r["confidence_threshold"] = float(r["confidence_threshold"])
                    
                    cate_name = d["Name"] if d["ParentName"] is not None and len(d["ParentName"]) > 0 else f'{d["ParentName"]}/{d["Name"]}'
                    d_confidence = "{:.2%}".format(d["Confidence"]/100)
                    rule_cates = ", ".join(r["categories"])
                    mod_result["result"].append({
                        "rule": r,
                        "moderation": d,
                        "description": f'Detected {cate_name} ({d_confidence}) content in the image, which voilates the rule: {rule_cates} ({r["confidence_threshold"]}% threshold)'
                    })
                    
                    if r.get("auto_stop", False) == True:
                        auto_stop = True

    safe = len(mod_result["result"]) == 0
    print(f"### 4.1 Evaluatino result: {safe}", mod_result)
    
    event["message"] = f'Safe content: {safe}'
    event["mod_result"] = mod_result
    event["safe"] = safe
    event["auto_stop"] = auto_stop

    return event
