from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct

def create_policy_s3(self, region, account_id, bucket_names):

    res = []
    for s in bucket_names:
        res.append (f"arn:aws:s3:::{s}")
        res.append (f"arn:aws:s3:::{s}/*")

    return  _iam.PolicyStatement(
            actions=[
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
            ],
            resources=res
        )
        
def create_policy_rekognition(self, region, account_id):
    return  _iam.PolicyStatement(
            actions=["rekognition:DetectModerationLabels"],
            resources=["*"]
        )


def create_policy_dynamodb(self, region, account_id, dynamo_tables):
    
    res = []
    for t in dynamo_tables:
        res.append(f"arn:aws:dynamodb:{region}:{account_id}:table/{t}")
        
    return  _iam.PolicyStatement(
            actions=["dynamodb:DeleteItem","dynamodb:Query", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:GetItem"],
            resources=res
        )

def create_policy_lambda_log(self, region, account_id):
    return  _iam.PolicyStatement(
            actions=["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
            resources=[f"arn:aws:logs:{region}:{account_id}:log-group:*"]
        )

def create_policy_lambda_invoke(self, region, account_id, lambda_fun_names):
    res = []
    for l in lambda_fun_names:
        res.append(f"arn:aws:lambda:{region}:{account_id}:function:{l}")

    return  _iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            resources=res
        )

def create_policy_ivs(self, region, account_id):
    return  _iam.PolicyStatement(
            actions=["ivs:GetChannel","ivs:GetStream","ivs:ListChannels", "ivs:ListStreams", "ivs:ListStreamSessions", "ivs:StopStream"],
            resources=["*"]
        )

def create_policy_sns(self, region, account_id, sns_topics):
    return  _iam.PolicyStatement(
            actions=["sns:Publish"],
            resources=[f"arn:aws:sns:{region}:{account_id}:*"]
        )

def create_policy_kms(self, region, account_id):
    return  _iam.PolicyStatement(
            actions=["kms:GenerateDataKey", "kms:Decrypt"],
            resources=[f"arn:aws:kms:{region}:{account_id}:key/*"]
        )

def create_policy_stepfunctions(self, region, account_id, state_machine_names):
    res = []
    for s in state_machine_names:
        #res.append(f"arn:aws:states:{region}:{account_id}:stateMachine/{s}")
        res.append(f"{s}")
        
    return  _iam.PolicyStatement(
            actions=["states:StartExecution"],
            resources=res
        )
        