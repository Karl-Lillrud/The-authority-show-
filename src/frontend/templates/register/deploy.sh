#!/bin/bash

# Variables
BUCKET_NAME="devpodmanager"
REGION="eu-north-1"
APP_NAME="php-registration-app"
ENV_NAME="php-registration-env"
ZIP_FILE="php-registration-app.zip"
ROLE_NAME="aws-elasticbeanstalk-ec2-role"
POLICY_NAME="eb-instance-policy"
INSTANCE_PROFILE_NAME="aws-elasticbeanstalk-ec2-role"
API_NAME="PHPRegistrationAPI"
STAGE_NAME="prod"

# Step 2: Create IAM Role for Elastic Beanstalk
echo "Creating IAM role for Elastic Beanstalk..."
aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://<(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
)

echo "Attaching policy to IAM role..."
aws iam put-role-policy --role-name $ROLE_NAME --policy-name $POLICY_NAME --policy-document file://<(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "logs:*",
                "cloudwatch:*",
                "autoscaling:*",
                "elasticbeanstalk:*",
                "apigateway:*",
                "lambda:*"
            ],
            "Resource": "*"
        }
    ]
}
EOF
)

echo "Creating instance profile for Elastic Beanstalk..."
aws iam create-instance-profile --instance-profile-name $INSTANCE_PROFILE_NAME
aws iam add-role-to-instance-profile --instance-profile-name $INSTANCE_PROFILE_NAME --role-name $ROLE_NAME

# Step 3: Prepare PHP Application for Elastic Beanstalk
echo "Preparing PHP application..."
mkdir -p php-app
cp register.php php-app/
cp send-invitation.php php-app/
cd php-app
zip -r ../$ZIP_FILE .
cd ..

# Step 4: Create Elastic Beanstalk Application and Environment
echo "Creating Elastic Beanstalk application..."
aws elasticbeanstalk create-application --application-name $APP_NAME

echo "Creating Elastic Beanstalk environment..."
aws elasticbeanstalk create-environment \
    --application-name $APP_NAME \
    --environment-name $ENV_NAME \
    --solution-stack-name "64bit Amazon Linux 2 v3.5.6 running PHP 8.0" \
    --option-settings file://<(cat <<EOF
[
    {
        "Namespace": "aws:autoscaling:launchconfiguration",
        "OptionName": "IamInstanceProfile",
        "Value": "$INSTANCE_PROFILE_NAME"
    },
    {
        "Namespace": "aws:autoscaling:launchconfiguration",
        "OptionName": "InstanceType",
        "Value": "t2.micro"
    },
    {
        "Namespace": "aws:elasticbeanstalk:application:environment",
        "OptionName": "PHP_MAX_UPLOAD_SIZE",
        "Value": "50M"
    }
]
EOF
)

# Step 5: Set Up API Gateway with CORS
echo "Creating API Gateway..."
API_ID=$(aws apigateway create-rest-api --name $API_NAME --region $REGION --query "id" --output text)
PARENT_RESOURCE_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[0].id" --output text)

echo "Creating POST resource..."
RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $PARENT_RESOURCE_ID --path-part "register" --query "id" --output text)

echo "Adding POST method with CORS headers..."
aws apigateway put-method --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method POST --authorization-type NONE

aws apigateway put-method-response --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method POST --status-code 200 \
--response-models '{"application/json":"Empty"}' \
--response-parameters '{"method.response.header.Access-Control-Allow-Origin":true, "method.response.header.Access-Control-Allow-Methods":true, "method.response.header.Access-Control-Allow-Headers":true}'

aws apigateway put-integration --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method POST \
--integration-http-method POST --type HTTP --uri "http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com/register.php"

aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method POST --status-code 200 \
--response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'*'"}'

echo "Deploying API Gateway..."
aws apigateway create-deployment --rest-api-id $API_ID --stage-name $STAGE_NAME

# Step 6: Deploy the Application
echo "Deploying application to Elastic Beanstalk..."
aws elasticbeanstalk create-application-version \
    --application-name $APP_NAME \
    --version-label "v1" \
    --source-bundle S3Bucket=$BUCKET_NAME,S3Key=$ZIP_FILE

aws elasticbeanstalk update-environment \
    --environment-name $ENV_NAME \
    --version-label "v1"

# Step 7: Output API Gateway Endpoint
echo "API Gateway endpoint deployed. Use this URL for POST requests:"
echo "https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME/register"
