from aws_cdk import (
    Stack,
    NestedStack,
    CfnParameter as _cfnParameter,
    aws_cognito as _cognito,
    aws_s3 as _s3,
    aws_s3_notifications as _s3_noti,
    aws_s3_deployment as _s3_deploy,
    aws_dynamodb as _dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as _apigw,
    aws_iam as _iam,
    aws_sns as _sns,
    Environment,
    Duration,
    aws_sns_subscriptions,
    aws_stepfunctions as _aws_stepfunctions,
    RemovalPolicy,
    custom_resources as cr,
    CfnOutput,
    CustomResource,
    Token,
    Fn,
    CfnResource
)
from aws_cdk.aws_logs import RetentionDays
from aws_cdk.aws_apigateway import IdentitySource
from aws_cdk.aws_kms import Key

from constructs import Construct
import os
import uuid
import json
from stack.constant import *

from iam_role.lambda_re_delete_config_role import create_role as lambda_re_delete_config_role
from iam_role.lambda_re_img_check_freq_role import create_role as lambda_re_img_check_freq_role
from iam_role.lambda_re_img_check_similarity_role import create_role as lambda_re_img_check_similarity_role
from iam_role.lambda_re_img_mod_eval_role import create_role as lambda_re_img_mod_eval_role
from iam_role.lambda_re_upsert_config_role import create_role as lambda_re_upsert_config_role
from iam_role.lambda_mo_get_streams_role import create_role as lambda_mo_get_streams_role
from iam_role.lambda_re_get_configs_role import create_role as lambda_re_get_configs_role
from iam_role.lambda_mo_ack_warning_role import create_role as lambda_mo_ack_warning_role
from iam_role.lambda_mo_get_channels_role import create_role as lambda_mo_get_channels_role
from iam_role.lambda_mo_sns_listener_role import create_role as lambda_mo_sns_listener_role
from iam_role.lambda_re_s3_listener_role import create_role as lambda_re_s3_listener_role
from iam_role.stepfunction_execution_role import create_role as stepfunction_execution_role

class BackendStack(NestedStack):
    account_id = None
    region = None
    instance_hash = None
    api_gw_base_url = None
    cognito_user_pool_id = None
    cognito_app_client_id = None
    s3_ivs_bucket_name = None
    
    def __init__(self, scope: Construct, construct_id: str, instance_hash_code, s3_ivs_bucket_name, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.account_id=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"])
        self.region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
        
        self.instance_hash = instance_hash_code #str(uuid.uuid4())[0:5]
        self.s3_ivs_bucket_name = s3_ivs_bucket_name

        s3_ivs_bucket, s3_ivs_bucket = None, None

        # IVS bucket: create if no given name
        if s3_ivs_bucket_name is None or len(s3_ivs_bucket_name) == 0:
            self.s3_ivs_bucket_name = f'{IVS_THUMBNAIL_S3_BUCKET}-{self.account_id}-{self.region}-{self.instance_hash}'
            s3_ivs_bucket = _s3.Bucket(self, "ivs-bucket", 
                bucket_name=self.s3_ivs_bucket_name,
                removal_policy=RemovalPolicy.DESTROY,
                auto_delete_objects=True)
        else:
            s3_ivs_bucket = _s3.Bucket.from_bucket_name(self, "ivs-bucket", s3_ivs_bucket_name)
                    
        # Create Cognitio User pool and authorizer
        user_pool = _cognito.UserPool(self, "web-user-pool",
            user_pool_name=f"{COGNITO_NAME_PREFIX}-{self.instance_hash}",
            self_sign_up_enabled=False,
            removal_policy=RemovalPolicy.DESTROY
        )
        self.cognito_user_pool_id = user_pool.user_pool_id

        web_client = user_pool.add_client("app-client", 
            auth_flows=_cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            supported_identity_providers=[_cognito.UserPoolClientIdentityProvider.COGNITO],
        )
        self.cognito_app_client_id = web_client.user_pool_client_id

        # Add the Cognito User Pool to the API Gateway instance as an authorizer
        auth = _apigw.CognitoUserPoolsAuthorizer(self, f"WebAuth-{self.instance_hash}", 
            cognito_user_pools=[user_pool],
            identity_source=IdentitySource.header('Authorization')
        )
                                                      
        # Create DynamoDB                                 
        config_table = _dynamodb.Table(self, 
            id='config-table', 
            table_name=f'{DYNAMO_CONFIG_TABLE}-{self.instance_hash}', 
            partition_key=_dynamodb.Attribute(name='channel_id', type=_dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY
        ) 
        cache_table = _dynamodb.Table(self, 
            id='cache-table', 
            table_name=f'{DYNAMO_CACHE_TABLE}-{self.instance_hash}', 
            partition_key=_dynamodb.Attribute(name='channel_id', type=_dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY
        ) 
        warning_table = _dynamodb.Table(self, 
            id='warning-table', 
            table_name=f'{DYNAMO_WARNING_TABLE}-{self.instance_hash}', 
            partition_key=_dynamodb.Attribute(name='id', type=_dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY
        ) 

        # Create a KMS key for the SNS topic
        sns_kms_key = Key(self, "sns-kms-key", enable_key_rotation=True)
        # Create SNS topic
        warning_topic = _sns.Topic(self, 
            id="sns-warning-topic", 
            display_name=SNS_WARNING_TOPIC_NAME_PREFIX,
            master_key=sns_kms_key
        )
        
        # Step Function - start
        # Lambda: cm-ls-rules-engine-image-flow-check-frequency
        lambda_re_img_check_freq = _lambda.Function(self, 
            id='re_img_check_freq', 
            function_name=f"cm-ls-rules-engine-image-flow-check-frequency-{self.instance_hash}", 
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler='cm-ls-rules-engine-image-flow-check-frequency.lambda_handler',
            code=_lambda.Code.from_asset(os.path.join("./", "lambda/rules-engine/cm-ls-rules-engine-image-flow-check-frequency")),
            timeout=Duration.seconds(30),
            role=lambda_re_img_check_freq_role(self,s3_ivs_bucket_name, self.region, self.account_id),
            environment={
             'DYNAMO_CONFIG_TABLE': DYNAMO_CONFIG_TABLE + f"-{self.instance_hash}",
             'DYNAMO_CACHE_TABLE': DYNAMO_CACHE_TABLE + f"-{self.instance_hash}",
            }
        )
        # Lambda: cm-ls-rules-engine-image-similarity-check 
        lambda_re_img_similiar_check = _lambda.DockerImageFunction(self,
            "imagehash_lamdba", 
            function_name=f"cm-ls-rules-engine-image-similarity-check-{self.instance_hash}", 
            #handler='cm-ls-rules-engine-image-similarity-check.lambda_handler',
            code=_lambda.DockerImageCode.from_image_asset(os.path.join("./", "lambda/rules-engine/cm-ls-rules-engine-image-similarity-check")),
            role=lambda_re_img_check_similarity_role(self,"", self.region, self.account_id),
            timeout=Duration.seconds(30),
            memory_size=1024,
            environment={
             'DYNAMO_CACHE_TABLE': DYNAMO_CACHE_TABLE + f"-{self.instance_hash}",
            },
        )

        # Lambda: cm-ls-rules-engine-image-flow-moderation-and-eval 
        lambda_re_img_mod_eval = _lambda.Function(self, 
            id='re-img-mod-eval', 
            function_name=f"cm-ls-rules-engine-image-flow-moderation-and-eval-{self.instance_hash}", 
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler='cm-ls-rules-engine-image-flow-moderation-and-eval.lambda_handler',
            code=_lambda.Code.from_asset(os.path.join("./", "lambda/rules-engine/cm-ls-rules-engine-image-flow-moderation-and-eval")),
            role=lambda_re_img_mod_eval_role(self,s3_ivs_bucket_name, self.region, self.account_id),
        )
        # StepFunctions StateMachine
        sm_json = None
        with open('./stepfunctions/cm-ls-rules-engine-image-flow/cm-ls-rules-engine-image-flow.json', "r") as f:
            sm_json = str(f.read())

        if sm_json is not None:
            sm_json = sm_json.replace("##LAMBDA_RE_IMG_CHECK_FREQ##", f"arn:aws:lambda:{self.region}:{self.account_id}:function:cm-ls-rules-engine-image-flow-check-frequency-{self.instance_hash}")
            sm_json = sm_json.replace("##LAMBDA_RE_IMG_CHECK_SIMILARITY##", f"arn:aws:lambda:{self.region}:{self.account_id}:function:cm-ls-rules-engine-image-similarity-check-{self.instance_hash}")
            sm_json = sm_json.replace("##LAMBDA_RE_IMG_MOD_EVAL##", f"arn:aws:lambda:{self.region}:{self.account_id}:function:cm-ls-rules-engine-image-flow-moderation-and-eval-{self.instance_hash}")
            sm_json = sm_json.replace("##SNS_RE_WARNING_TOPIC##", warning_topic.topic_arn)

        cfn_state_machine = _aws_stepfunctions.CfnStateMachine(self, 'stepfunction-image-workflow',
            state_machine_name=f'{STEP_FUNCTION_STATE_MACHINE_NAME_PREFIX}-{self.instance_hash}', 
            role_arn=stepfunction_execution_role(self, s3_ivs_bucket_name, self.region, self.account_id).role_arn,
            definition_string=sm_json)
        # Step Function - end
        
        # API Gateway - start
        api = _apigw.RestApi(self, f"{API_NAME_PREFIX}-{self.instance_hash}",
                                  rest_api_name=f"{API_NAME_PREFIX}-{self.instance_hash}")
        v1 = api.root.add_resource("v1")
        re = v1.add_resource("rules-engine")
        mo = v1.add_resource("monitoring")
        
        self.api_gw_base_url = api.url
        CfnOutput(self, id="CmLsApiGwBaseUrl", value=api.url, export_name="CmLsApiGwBaseUrl")
                                     
        # POST v1/rules-engine/config-delete
        # Lambda: cm-ls-rules-engine-delete-configs
        self.create_api_endpoint(id='re-delete-configs', 
            root=re, path1="rules-engine", path2="config-delete", method="POST", auth=auth, 
            role=lambda_re_delete_config_role(self, s3_ivs_bucket_name, self.region, self.account_id), 
            lambda_file_name="cm-ls-rules-engine-delete-configs", 
            instance_hash=self.instance_hash, memory_m=128, timeout_s=10, 
            evns={
             'DYNAMO_CONFIG_TABLE': DYNAMO_CONFIG_TABLE + f"-{self.instance_hash}",
             'DYNAMO_CACHE_TABLE': DYNAMO_CACHE_TABLE + f"-{self.instance_hash}",
            })   

        # POST /v1/rules-engine/config-upsert
        # Lambda: cm-ls-rules-engine-upsert-config
        self.create_api_endpoint('re-updsert-coonfig', re, "rules-engine", "config-upsert", "POST", auth, lambda_re_upsert_config_role(self, s3_ivs_bucket_name, self.region, self.account_id), "cm-ls-rules-engine-upsert-config", self.instance_hash, 128, 10, 
            evns={
             'DYNAMO_CONFIG_TABLE': DYNAMO_CONFIG_TABLE + f"-{self.instance_hash}",
             'DYNAMO_CACHE_TABLE': DYNAMO_CACHE_TABLE + f"-{self.instance_hash}",
            })        
            
        # POST /v1/rules-engine/configs
        # Lambda: cm-ls-rules-engine-get-configs
        self.create_api_endpoint('re-get-configs', re, "rules-engine", "configs", "POST", auth, lambda_re_get_configs_role(self, s3_ivs_bucket_name, self.region, self.account_id), "cm-ls-rules-engine-get-configs", self.instance_hash, 128, 10, 
            evns={
             'DYNAMO_CONFIG_TABLE': DYNAMO_CONFIG_TABLE + f"-{self.instance_hash}",
            })


        # POST /v1/monitoring/streams
        # Lambda: cm-ls-monitor-service-get-streams 
        self.create_api_endpoint('mo-get-streams', mo, "monitoring", "streams", "POST", auth, 
                lambda_mo_get_streams_role(self, s3_ivs_bucket_name, self.region, self.account_id), 
                "cm-ls-monitor-service-get-streams", self.instance_hash, 128, 30, 
                evns={
                'DYNAMO_WARNING_TABLE': DYNAMO_WARNING_TABLE + f"-{self.instance_hash}",                
                'IVS_THUMBNAIL_PREFIX': IVS_THUMBNAIL_PREFIX,
                'ACK_SLA_S': ACK_SLA_S,
                'S3_PRE_SIGNED_URL_EXPIRY_S': S3_PRE_SIGNED_URL_EXPIRY_S,
                'DYNAMO_WARNING_TABLE': DYNAMO_WARNING_TABLE+ f"-{self.instance_hash}",
                'DYNAMO_CACHE_TABLE': DYNAMO_CACHE_TABLE + f"-{self.instance_hash}",
                })      
            
        # POST /v1/monitoring/acknowledge
        # Lambda: cm-ls-monitor-service-ack-warning
        self.create_api_endpoint('mo-ack-warning', mo, "monitoring", "acknowledge", "POST", auth, lambda_mo_ack_warning_role(self, s3_ivs_bucket_name, self.region, self.account_id), "cm-ls-monitor-service-ack-warning", self.instance_hash, 128, 3, 
            evns={
             'DYNAMO_WARNING_TABLE': DYNAMO_WARNING_TABLE + f"-{self.instance_hash}",
            })

        # POST /v1/monitoring/channels
        # Lamabd: cm-ls-monitor-service-get-channels 
        self.create_api_endpoint('mo-get-channels', mo, "monitoring", "channels", "POST", auth, lambda_mo_get_channels_role(self, s3_ivs_bucket_name, self.region, self.account_id), "cm-ls-monitor-service-get-channels", self.instance_hash, 128, 10, 
            evns={
             'DYNAMO_CONFIG_TABLE': DYNAMO_CONFIG_TABLE + f"-{self.instance_hash}", 
             'IVS_THUMBNAIL_S3_BUCKET': s3_ivs_bucket_name,
             "IVS_THUMBNAIL_PREFIX": IVS_THUMBNAIL_PREFIX,
             'S3_PRE_SIGNED_URL_EXPIRY_S': S3_PRE_SIGNED_URL_EXPIRY_S,
            })
        # API Gateway - end
            
        # Monitoring service SNS listener
        # Lambda: cm-ls-monitor-service-listener 
        lambda_mo_sns_listener = _lambda.Function(self, 
            id='monitor-sns-listener', 
            function_name=f"cm-ls-monitor-service-listener-{self.instance_hash}", 
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler='cm-ls-monitor-service-listener.lambda_handler',
            code=_lambda.Code.from_asset(os.path.join("./", "lambda/monitoring/cm-ls-monitor-service-listener")),
            timeout=Duration.seconds(30),
            role=lambda_mo_sns_listener_role(self, s3_ivs_bucket_name, self.region, self.account_id),
            environment={
             'DYNAMO_WARNING_TABLE': DYNAMO_WARNING_TABLE + f"-{self.instance_hash}",
            }
        )
        # Subscribe to Warning SNS topic
        warning_topic.add_subscription(aws_sns_subscriptions.LambdaSubscription(lambda_mo_sns_listener))

        # IVS thumbnail S3 trigger
        # Lambda: cm-ls-rules-engine-image-s3-listener 
        lambda_re_s3_listener = _lambda.Function(self, 
            id='re-s3-listener', 
            function_name=f"cm-ls-rules-engine-image-s3-listener-{self.instance_hash}", 
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler='cm-ls-rules-engine-image-s3-listener.lambda_handler',
            code=_lambda.Code.from_asset(os.path.join("./", "lambda/rules-engine/cm-ls-rules-engine-image-s3-listener")),
            timeout=Duration.seconds(10),
            role=lambda_re_s3_listener_role(self, s3_ivs_bucket_name, self.region, self.account_id),
            environment={
             'IMAGE_PROCESSOR_WORKFLOW_ARN': cfn_state_machine.attr_arn,
            }
        )

        if s3_ivs_bucket is not None and s3_ivs_bucket.bucket_name is not None and len(s3_ivs_bucket.bucket_name) > 0:
            # Grand S3 access to trigger the Lambda function
            s3_ivs_bucket.grant_read(lambda_re_s3_listener)
            # Subscribe to S3 file creat event
            s3_ivs_bucket.add_object_created_notification(
                _s3_noti.LambdaDestination(lambda_re_s3_listener),
                _s3.NotificationKeyFilter(prefix=IVS_THUMBNAIL_PREFIX, suffix=IVS_THUMBNAIL_SUFFIX)
            )

    def create_api_endpoint(self, id, root, path1, path2, method, auth, role, lambda_file_name, instance_hash, memory_m, timeout_s, evns, layer=None):
        layers = []
        if layer is not None:
            layers = [layer]
        lambda_funcation = _lambda.Function(self, 
            id=id, 
            function_name=f"{lambda_file_name}-{self.instance_hash}", 
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler=f'{lambda_file_name}.lambda_handler',
            code=_lambda.Code.from_asset(os.path.join("./", f"lambda/{path1}/{lambda_file_name}")),
            timeout=Duration.seconds(timeout_s),
            role=role,
            memory_size=memory_m,
            environment=evns,
            layers=layers
        )   
        
        resource = root.add_resource(
                path2, 
                default_cors_preflight_options=_apigw.CorsOptions(
                allow_methods=['POST', 'OPTIONS'],
                allow_origins=_apigw.Cors.ALL_ORIGINS)
        )
        method = resource.add_method(
            method, 
            _apigw.LambdaIntegration(
                lambda_funcation,
                proxy=False,
                integration_responses=[
                    _apigw.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            'method.response.header.Access-Control-Allow-Origin': "'*'"
                        }
                    )
                ]
            ),
            method_responses=[
                _apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    }
                )
            ],
            authorizer=auth,
            authorization_type=_apigw.AuthorizationType.COGNITO
        )