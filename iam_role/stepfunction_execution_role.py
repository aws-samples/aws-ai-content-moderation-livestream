from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct
from iam_role import policy


def create_role(self, bucket_name, region, account_id):
    # IAM role
    new_role = _iam.Role(self, "stepfunction_execution_role",
        assumed_by=_iam.CompositePrincipal(
                _iam.ServicePrincipal("lambda.amazonaws.com"),
                _iam.ServicePrincipal("states.amazonaws.com")
            ),
    )
    new_role.add_to_policy(
        # Lambda invoke access
        policy.create_policy_lambda_invoke(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # SNS access
        policy.create_policy_sns(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # IVS access
        policy.create_policy_ivs(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # CloudWatch log
        policy.create_policy_lambda_log(self, bucket_name, region, account_id)
    )
    new_role.add_to_policy(
        # Step function pass role
        policy.create_policy_passrole_stepfunctions(self, bucket_name, region, account_id)
    )
    
    return new_role