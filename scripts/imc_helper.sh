#!/bin/sh

# Initial Variable Setup
script_directory=`pwd`
cd ..
current_directory=`pwd`
time_stamp=`date "+%H%M%S%N"`
pid=$$
imc_bucket_name='imc'${time_stamp}${pid}
echo $imc_bucket_name
EC2_AVAIL_ZONE=`curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone`
EC2_REGION="`echo \"$EC2_AVAIL_ZONE\" | sed 's/[a-z]$//'`"

#. Creating an EC2 Keypair
aws ec2 create-key-pair --key-name ${imc_bucket_name} > "ec2key_"${imc_bucket_name}

# Creating service linked role for sitewise
aws iam create-service-linked-role --aws-service-name iotsitewise.amazonaws.com

# Creating S3 bucket and uploading files
aws s3api create-bucket --bucket ${imc_bucket_name} --region ${EC2_REGION} --create-bucket-configuration LocationConstraint=${EC2_REGION}
aws s3 cp ./ s3://${imc_bucket_name}/quickstart/ --recursive
#echo "aws s3api delete-bucket --bucket "${imc_bucket_name}" --region "${EC2_REGION}
echo "************************"
echo "**** Copy and paste the below url for workload cloudformation temaplte ****"
echo "https://"${imc_bucket_name}".s3."${EC2_REGION}".amazonaws.com/quickstart/templates/IMC-workload.template.yaml"
echo "************************"
echo "################"
echo "#### To Delete your assets and bucket #####"
echo "aws s3 rb s3://"${imc_bucket_name}" --force"
echo "################"
cd ${script_directory}
