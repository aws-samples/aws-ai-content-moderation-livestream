COGNITO_NAME_PREFIX = "cm-livestream-user-pool"

SNS_WARNING_TOPIC_NAME_PREFIX = "cm-livestream-warning"

DYNAMO_CONFIG_TABLE = 'cm-livestream-config'
DYNAMO_CACHE_TABLE = 'cm-livestream-cache'
DYNAMO_WARNING_TABLE = 'cm-livestream-warning'
DYNAMO_DEFAULT_GLOBAL_RULE = '{"channel_id":"98382fe5-7141-4cea-994d-fc4b938a7cd1","global_flag":true,"channel_name_regex":".*","name":"Default global config","image":{"api":"rekognition_image_moderation_api","sample_frequency_s":60,"ignore_similar":true,"image_hash_threshold":10,"rules":[{"id":"1400d86d-fed1-4199-9447-4852bbb1c874","name":"All categories","categories":["Explicit Nudity","Suggestive","Violence","Visually Disturbing","Rude Gestures","Drugs","Tobacco","Alcohol","Gambling","Hate Symbols"],"confidence_threshold":60,"auto_stop":false}]},"description":"Default configuration applies to all channels which sample every 60 seconds and encompasses all moderation categories with a confidence threshold set at 60%.","priority":3}'

STEP_FUNCTION_STATE_MACHINE_NAME_PREFIX = 'cm-livestream-rules-engine-image-flow'

API_NAME_PREFIX = 'cm-livstream-web-service'

IVS_THUMBNAIL_S3_BUCKET = 'wwso-cm-livestream-demo'
IVS_THUMBNAIL_PREFIX = "ivs/v1/" # Template: "ivs/v1/{account_id}/{channel_id}/{year}/{month}/{day}/{hour}/{minute}/{recording_id}"
IVS_THUMBNAIL_SUFFIX = ".jpg"

ACK_SLA_S = "60" # Monitoring service moderator acknowledge SLA time in second
S3_PRE_SIGNED_URL_EXPIRY_S = "3600" # 1 hour: for warning images

S3_IVS_BUCKET_NAME_PREFIX = 'cm-livestream-ivs-thumbnail'
S3_WEB_BUCKET_NAME_PREFIX = 'cm-livestream-web'
S3_TEMP_BUCKET_NAME_PREFIX = 'cm-livestream-temp'
S3_ASSET_LAMBDA_LAYER_BUCKET_NAME = "sagemaker-us-west-2-122702569249"#"comprehend-assets-wwso"#
S3_ASSET_LAMBDA_LAYER_KEY = "imagehash.zip"#"cdk-assset/lambda-layer-imagehash.zip"#
