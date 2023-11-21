from aws_cdk import (
    Stack,
    aws_iam as _iam,
)
from constructs import Construct
from iam_role import policy


def create_role(self, region, account_id, stepfunctions):
    # IAM role
    new_role = _iam.Role(self, "lambda-re-s3-listener-role",
        assumed_by=_iam.CompositePrincipal(
                _iam.ServicePrincipal("lambda.amazonaws.com"),
                _iam.ServicePrincipal("states.amazonaws.com")
            ),
    )
    new_role.add_to_policy(
        # CloudWatch log
        policy.create_policy_lambda_log(self, region, account_id)
    )
    new_role.add_to_policy(
        # Invoke stepfunctions
        policy.create_policy_stepfunctions(self, region, account_id, stepfunctions)
    )
    
    return new_role