#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import CfnParameter as _cfnParameter
from aws_cdk import Stack,CfnOutput
from aws_cdk import aws_s3 as _s3
from aws_cdk import Duration
import uuid
from stack.backend_stack import BackendStack
from stack.frontend_stack import FrontendStack
from stack.constant import *

env = cdk.Environment(account="TARGET_ACCOUNT_ID", region="TARGET_REGION")

class RootStack(Stack):
    instance_hash = None
    ivs_bucket_name = None
    user_emails = None

    def __init__(self, scope):
        super().__init__(scope, "CmLiveStreamRootStack", description="AWS live stream moderation Stack stack. Beta",
        )
    
        self.instance_hash = str(uuid.uuid4())[0:5]

        input_ivs_bucket_name = _cfnParameter(self, "inputIvsBucketName", type="String",
                                        description="The S3 bucket holds IVS recording thumbnails. This sets up an empty bucket for IVS recording if you don't provide one.")
        input_user_emails = _cfnParameter(self, "inputUserEmails", type="String",
                                description="Use your email to log in to the web portal. Split by comma if there are multiple emails.")
        
        if input_ivs_bucket_name is not None:
            self.ivs_bucket_name = input_ivs_bucket_name.value_as_string
        if input_user_emails is not None:
            self.user_emails = input_user_emails.value_as_string
        
        backend_stack = BackendStack(self, "BackendStack", description="AWS livestream moderation - Backend deployment statck.",
            instance_hash_code=self.instance_hash,
            s3_ivs_bucket_name = self.ivs_bucket_name,
            timeout = Duration.hours(2)
        )
        
        frontend_stack = FrontendStack(self, "FrontStack", description="AWS livestream moderatio - Frontend deployment statck.",
            instance_hash_code=self.instance_hash,
            api_gw_base_url = backend_stack.api_gw_base_url,
            cognito_user_pool_id = backend_stack.cognito_user_pool_id,
            cognito_app_client_id = backend_stack.cognito_app_client_id,
            user_emails = self.user_emails,
        )
        frontend_stack.node.add_dependency(backend_stack)

        CfnOutput(self, "Website URL",
            value=f"https://{frontend_stack.output_url}"
        )
        if self.ivs_bucket_name is None:
            # Created IVS S3 bucket
            CfnOutput(self, "S3 Bucket for IVS",
                value=backend_stack.s3_ivs_bucket_name
            )

app = cdk.App()

root_stack = RootStack(app)

app.synth()