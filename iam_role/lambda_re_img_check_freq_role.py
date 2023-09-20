from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct
from iam_role import policy


def create_role(self, bucket_name, region, account_id):
    # IAM role
    new_role = _iam.Role(self, "lambda-re-img-check-freq-role",
        assumed_by=_iam.CompositePrincipal(
                _iam.ServicePrincipal("lambda.amazonaws.com"),
                _iam.ServicePrincipal("states.amazonaws.com")
            ),
    )
    new_role.add_to_policy(
        # StepFunctions assumed rule
        policy.create_policy_passrole_stepfunctions(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # DynamoDB access
        policy.create_policy_dynamodb(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # S3 access
        policy.create_policy_s3(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # CloudWatch log
        policy.create_policy_lambda_log(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # IVS
        policy.create_policy_ivs(self, bucket_name, region, account_id)
    )
    return new_role