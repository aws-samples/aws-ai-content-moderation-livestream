from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct
from iam_role import policy


def create_role(self, region, account_id, s3_buckets, dynam_tables):
    # Trust
    new_role = _iam.Role(self, "lambda-provision-web-role",
        assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"),
    )
    # Log groups
    new_role.add_to_policy(
        policy.create_policy_lambda_log(self, region, account_id)
    )
    # Cognito
    new_role.add_to_policy(
        _iam.PolicyStatement(
            actions=["cognito-idp:AdminCreateUser"],
            resources=["*"]
        )
    )
    # S3
    new_role.add_to_policy(
        policy.create_policy_s3(self, region, account_id, s3_buckets)
    )
    # DynamoDB
    new_role.add_to_policy(
        policy.create_policy_dynamodb(self, region, account_id, dynam_tables)
    )
    # CloudFront
    new_role.add_to_policy(
        _iam.PolicyStatement(
            actions=["cloudfront:CreateInvalidation"],
            resources=["*"]
        )
    )

    new_role.add_to_policy(
        _iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            resources=["*"]
        )
    )
    return new_role