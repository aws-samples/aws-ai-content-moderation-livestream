from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct
from iam_role import policy


def create_role(self, region, account_id, s3_buckets, sns_topics, lambda_fun_names):
    # IAM role
    new_role = _iam.Role(self, "stepfunction_execution_role",
        assumed_by=_iam.CompositePrincipal(
                _iam.ServicePrincipal("lambda.amazonaws.com"),
                _iam.ServicePrincipal("states.amazonaws.com")
            ),
    )
    new_role.add_to_policy(
        # Lambda invoke access
        policy.create_policy_lambda_invoke(self, region, account_id, lambda_fun_names)
    )
    new_role.add_to_policy(
        # SNS access
        policy.create_policy_sns(self, region, account_id, sns_topics)
    )
    new_role.add_to_policy(
        # KMS access
        policy.create_policy_kms(self, region, account_id)
    )
    new_role.add_to_policy(
        # IVS access
        policy.create_policy_ivs(self, region, account_id)
    )
    new_role.add_to_policy(
        # CloudWatch log
        policy.create_policy_lambda_log(self, region, account_id)
    )
    
    return new_role