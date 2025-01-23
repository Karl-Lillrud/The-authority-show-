#!/bin/bash

# Variables
BUCKET_NAME="my-registration-app-bucket"
REGION="us-east-1"
APP_NAME="php-registration-app"
ENV_NAME="php-registration-env"
ZIP_FILE="php-registration-app.zip"
ROLE_NAME="eb-instance-role"
POLICY_NAME="eb-instance-policy"
INSTANCE_PROFILE_NAME="eb-instance-profile"

# Step 1: Create S3 Bucket for Static Files
echo "Creating S3 bucket..."
aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION --create-bucket-configuration LocationConstraint=$REGION

# Enable Static Website Hosting
echo "Enabling static website hosting on S3..."
aws s3 website s3://$BUCKET_NAME/ --index-document register.html --error-document register.html

# Upload Static Files to S3 Bucket
echo "Uploading static files to S3..."
aws s3 cp register.html s3://$BUCKET_NAME/
aws s3 cp waitinglist/index.html s3://$BUCKET_NAME/waitinglist/
aws s3 cp waitinglist/server.js s3://$BUCKET_NAME/waitinglist/

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
                "elasticbeanstalk:*"
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
cp waitinglist/send-invitation.php php-app/
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

# Step 5: Deploy the Application
echo "Deploying application to Elastic Beanstalk..."
aws elasticbeanstalk create-application-version \
    --application-name $APP_NAME \
    --version-label "v1" \
    --source-bundle S3Bucket=$BUCKET_NAME,S3Key=$ZIP_FILE

aws elasticbeanstalk update-environment \
    --environment-name $ENV_NAME \
    --version-label "v1"

# Step 6: Output Elastic Beanstalk Environment URL
echo "Elastic Beanstalk environment deployed. Access your application using:"
aws elasticbeanstalk describe-environments --application-name $APP_NAME --query "Environments[0].CNAME" --output text
