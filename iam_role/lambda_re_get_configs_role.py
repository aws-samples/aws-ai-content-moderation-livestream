from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct
from iam_role import policy


def create_role(self, region, account_id, dynamo_tables):
    # IAM role
    new_role = _iam.Role(self, "lambda-mo-get-configs-role",
        assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"),
    )
    new_role.add_to_policy(
        # DynamoDB access
        policy.create_policy_dynamodb(self, region, account_id, dynamo_tables)
    )
    new_role.add_to_policy(
        # CloudWatch log
        policy.create_policy_lambda_log(self, region, account_id)
    )
    return new_role