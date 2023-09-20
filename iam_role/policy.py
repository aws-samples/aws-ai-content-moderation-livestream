from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct

def create_policy_s3(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["s3:*", "s3:GetObject", "s3:PutObject"],
            resources=["*"]
        )

def create_policy_passrole_rekognition(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["iam:PassRole"],
            resources=["*"],
            conditions={
                "StringEquals": {
                    "iam:PassedToService": "rekognition.amazonaws.com"
                }
            }
        )
def create_policy_passrole_stepfunctions(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["iam:PassRole"],
            resources=["*"],
            conditions={
                "StringEquals": {
                    "iam:PassedToService": "states.amazonaws.com"
                }
            }
        )
        
def create_policy_rekognition(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["rekognition:DetectModerationLabels"],
            resources=["*"]
        )


def create_policy_dynamodb(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["dynamodb:*"],
            resources=["*"]
        )

def create_policy_lambda_log(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
            resources=[f"arn:aws:logs:{region}:{account_id}:*"]
        )

def create_policy_lambda_invoke(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            resources=[f"*"]
        )

def create_policy_ivs(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["ivs:GetChannel","ivs:GetStream","ivs:ListChannels", "ivs:ListStreams", "ivs:ListStreamSessions", "ivs:StopStream"],
            resources=["*"]
        )

def create_policy_sns(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["sns:*", "kms:GenerateDataKey", "kms:Decrypt"],
            resources=["*"]
        )

def create_policy_stepfunctions(self, bucket_name, region, account_id):
    return  _iam.PolicyStatement(
            actions=["states:StartExecution"],
            resources=["*"]
        )
        