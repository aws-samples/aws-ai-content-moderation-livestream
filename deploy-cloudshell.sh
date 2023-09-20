# Install Node CDK package
sudo npm install -g aws-cdk

# Create Python Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

# install docker - to build the Lambda docker imageI have limited knowledge of Doc verification. But I think it also missed the piece integrating with the government database. To built a solution, we cannot only do AI.
sudo yum update -y
sudo amazon-linux-extras install -y docker
sudo service docker start

# Bootstrap CDK - this step will launch a CloudFormation stack to provision the CDK package, which will take ~2 minutes.
cdk bootstrap aws://${CDK_DEFAULT_ACCOUNT}/${CDK_DEFAULT_REGION}

# Deploy CDK package - this step will launch one CloudFormation stack with three nested stacks for different sub-systems, which will take ~10 minutes.
cdk deploy --parameters inputIvsBucketName=${CDK_INPUT_IVS_RECORDING_S3_BUCKET} --parameters inputUserEmails=${CDK_INPUT_USER_EMAILS}  --requires-approval never  --all
