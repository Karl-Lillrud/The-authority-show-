#!/bin/bash

# Exit on error
set -e

# Variables
APP_NAME="php-registration-app"
ENV_NAME="php-registration-env"
VERSION_LABEL="v1"
S3_BUCKET="devpodmanager"
ZIP_FILE="php-registration-app.zip"
ROLE_NAME="aws-elasticbeanstalk-ec2-role"
INSTANCE_PROFILE="aws-elasticbeanstalk-ec2-role"
REGION="eu-north-1"

# Create IAM Role and Instance Profile
if ! aws iam get-role --role-name $ROLE_NAME > /dev/null 2>&1; then

  echo "Creating IAM Role: $ROLE_NAME"
  aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file://trust-policy.json

  echo "Attaching policies to IAM Role"
  aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AWSElasticBeanstalkFullAccess

fi

if ! aws iam get-instance-profile --instance-profile-name $INSTANCE_PROFILE > /dev/null 2>&1; then

  echo "Creating Instance Profile: $INSTANCE_PROFILE"
  aws iam create-instance-profile --instance-profile-name $INSTANCE_PROFILE
  aws iam add-role-to-instance-profile --instance-profile-name $INSTANCE_PROFILE --role-name $ROLE_NAME

fi

# Package Application
if [ -f "$ZIP_FILE" ]; then

  rm "$ZIP_FILE"

fi
echo "Packaging application into $ZIP_FILE"
zip -r "$ZIP_FILE" . -x "*.git*" "deploy.sh" 

# Upload to S3
if ! aws s3 ls "s3://$S3_BUCKET/" > /dev/null 2>&1; then

  echo "Creating S3 bucket: $S3_BUCKET"
  aws s3 mb "s3://$S3_BUCKET" --region $REGION

fi
echo "Uploading $ZIP_FILE to S3 bucket: $S3_BUCKET"
aws s3 cp "$ZIP_FILE" "s3://$S3_BUCKET/"

# Create Elastic Beanstalk Application
if ! aws elasticbeanstalk describe-applications --application-names $APP_NAME > /dev/null 2>&1; then

  echo "Creating Elastic Beanstalk application: $APP_NAME"
  aws elasticbeanstalk create-application --application-name $APP_NAME

fi

# Create Elastic Beanstalk Environment
if ! aws elasticbeanstalk describe-environments --application-name $APP_NAME --environment-names $ENV_NAME > /dev/null 2>&1; then

  echo "Creating Elastic Beanstalk environment: $ENV_NAME"
  aws elasticbeanstalk create-environment \
    --application-name $APP_NAME \
    --environment-name $ENV_NAME \
    --solution-stack-name "64bit Amazon Linux 2 v3.3.6 running PHP 8.0" \
    --version-label $VERSION_LABEL \
    --option-settings file://option-settings.json

else

  echo "Updating Elastic Beanstalk environment: $ENV_NAME"
  aws elasticbeanstalk update-environment \
    --environment-name $ENV_NAME \
    --version-label $VERSION_LABEL

fi

# Create API Gateway (if required)
# Add your API Gateway setup logic here if it is still needed.

echo "Deployment completed successfully. Access your application via Elastic Beanstalk."
