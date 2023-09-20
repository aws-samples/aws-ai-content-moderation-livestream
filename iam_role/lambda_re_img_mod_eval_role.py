from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct
from iam_role import policy


def create_role(self, bucket_name, region, account_id):
    # IAM role
    new_role = _iam.Role(self, "lambda-re-img-mod-eval-role",
        assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"),
    )
    new_role.add_to_policy(
        policy.create_policy_passrole_rekognition(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # Rekognition access
        policy.create_policy_rekognition(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # S3 access
        policy.create_policy_s3(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # CloudWatch log
        policy.create_policy_lambda_log(self, bucket_name, region, account_id)
    )
    return new_role