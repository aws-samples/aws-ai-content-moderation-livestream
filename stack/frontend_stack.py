import os
from aws_cdk import (
    aws_iam as _iam,
    aws_s3 as _s3,
    aws_s3_deployment as _s3_deployment,
    aws_cloudfront as _cloudfront,
    aws_cloudfront_origins as _origins,
    aws_lambda as _lambda,
    Stack,
    CfnOutput,
    RemovalPolicy,
    CustomResource,
    Duration,
    custom_resources as cr,
    NestedStack,
)
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct
from iam_role.lambda_provision_web_role import create_role as create_provision_web_role
from stack.constant import *


class FrontendStack(NestedStack):
    instance_hash = None
    region = None
    account_id = None
    api_gw_base_url = None
    cognito_user_pool_id = None
    cognito_app_client_id = None
    user_emails = None
    
    output_url = ""

    def __init__(self, scope: Construct, construct_id: str, instance_hash_code, api_gw_base_url, cognito_user_pool_id, cognito_app_client_id, user_emails, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.instance_hash = instance_hash_code #str(uuid.uuid4())[0:5]
        
        self.account_id=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"])
        self.region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
        
        self.api_gw_base_url = api_gw_base_url
        self.cognito_user_pool_id = cognito_user_pool_id
        self.cognito_app_client_id = cognito_app_client_id

        self.user_emails = user_emails
        
        web_bucket = _s3.Bucket(
            self,
            id="cm-livestream-moderation-website",
            bucket_name=f'{S3_WEB_BUCKET_NAME_PREFIX}-{self.account_id}-{self.region}-{self.instance_hash}',
            access_control=_s3.BucketAccessControl.PRIVATE,
            website_index_document="index.html",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        
        _s3_deployment.BucketDeployment(
            self,
            id="cm-livestream-web-bucket-deploy",
            sources=[_s3_deployment.Source.asset("./web/build")],
            destination_bucket=web_bucket)
        
        # CloudFront Distribution
        cf_oai = _cloudfront.OriginAccessIdentity(self, 'CloudFrontOriginAccessIdentity')
 
        web_bucket.add_to_resource_policy(_iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[web_bucket.arn_for_objects('*')],
            principals=[_iam.CanonicalUserPrincipal(
                cf_oai.cloud_front_origin_access_identity_s3_canonical_user_id
            )]
        ))
        
        cf_dist = _cloudfront.CloudFrontWebDistribution(self, "cm-livestream-web-cloudfront-dist",
            origin_configs=[
                _cloudfront.SourceConfiguration(
                    s3_origin_source=_cloudfront.S3OriginConfig(
                        s3_bucket_source=web_bucket,
                        origin_access_identity=cf_oai
                    ),
                    behaviors=[_cloudfront.Behavior(is_default_behavior=True)]
                )
            ],
            default_root_object="index.html"
        )

        
        self.output_url = cf_dist.distribution_domain_name
        CfnOutput(self, id="CmLsCloudFrontWebsiteUrl", value=self.output_url, export_name="CmLsCloudFrontWebsiteUrl")

        # Custom Resource Lambda: cm-ls-provision-custom-resource
        # Replace APIGateway URL and Cognitio keys in S3 static website 
        provision_web_role = create_provision_web_role(self,web_bucket.bucket_name, self.region, self.account_id)
        lambda_provision = _lambda.Function(self, 
            id='provision-update-web-urls', 
            function_name=f"cm-ls-provision-custom-resource-{self.instance_hash}", 
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler='cm-ls-provision-custom-resource.on_event',
            code=_lambda.Code.from_asset(os.path.join("./", "lambda/provision-web")),
            timeout=Duration.seconds(120),
            role=provision_web_role,
            memory_size=512,
            environment={
             'APIGW_URL_PLACE_HOLDER': '[[[APIGATEWAY_BASE_URL]]]',
             'COGNITO_USER_POOL_ID_PLACE_HOLDER':'[[[COGNITO_USER_POOL_ID]]]',
             'COGNITO_USER_IDENTITY_POOL_ID_PLACE_HOLDER': '[[[COGNITO_IDENTITY_POOL_ID]]]',
             'COGNITO_REGION_PLACE_HOLDER': '[[[COGNITO_REGION]]]',
             'COGNITO_USER_POOL_CLIENT_ID_PLACE_HOLDER':'[[[COGNITO_USER_POOL_CLIENT_ID]]]',
             'COGNITO_USER_POOL_ID': self.cognito_user_pool_id,
             'COGNITO_USER_POOL_CLIENT_ID': self.cognito_app_client_id,
             'APIGW_URL': api_gw_base_url + 'v1',
             'COGNITO_REGION': self.region,
             'COGNITO_USER_IDENTITY_POOL_ID': '',
             'S3_WEB_BUCKET_NAME': web_bucket.bucket_name,
             'S3_JS_PREFIX': 'static/js/',
             'CLOUD_FRONT_DISTRIBUTION_ID': cf_dist.distribution_id,
             'COGNITO_USER_EMAILS': self.user_emails,
             'DYNAMO_CONFIG_TABLE': f'{DYNAMO_CONFIG_TABLE}-{self.instance_hash}',
             'DYNAMO_DEFAULT_GLOBAL_RULE': DYNAMO_DEFAULT_GLOBAL_RULE
            }
        )

        c_resource = cr.AwsCustomResource(
            self,
            f"provision-web-provider-{self.instance_hash}",
            log_retention=RetentionDays.ONE_WEEK,
            on_create=cr.AwsSdkCall(
                service="Lambda",
                action="invoke",
                physical_resource_id=cr.PhysicalResourceId.of("Trigger"),
                parameters={
                    "FunctionName": lambda_provision.function_name,
                    "InvocationType": "RequestResponse",
                    "Payload": "{\"RequestType\": \"Create\"}"
                },
                output_paths=["Payload"]
            ),
            role=provision_web_role
        )     