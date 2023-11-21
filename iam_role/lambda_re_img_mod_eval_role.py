from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct
from iam_role import policy


def create_role(self, region, account_id, s3_buckets):
    # IAM role
    new_role = _iam.Role(self, "lambda-re-img-mod-eval-role",
        assumed_by=_iam.CompositePrincipal(
                _iam.ServicePrincipal("lambda.amazonaws.com"),
                _iam.ServicePrincipal("rekognition.amazonaws.com")
            ),
    )
    new_role.add_to_policy(
        # Rekognition access
        policy.create_policy_rekognition(self, region, account_id)
    )
    new_role.add_to_policy(
        # S3 access
        policy.create_policy_s3(self, region, account_id, s3_buckets)
    )
    new_role.add_to_policy(
        # CloudWatch log
        policy.create_policy_lambda_log(self, region, account_id)
    )
    return new_role