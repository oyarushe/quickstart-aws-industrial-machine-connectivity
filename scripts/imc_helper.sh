#!/bin/sh

# Make sure we're working in IMC-Kit approved region
VIRGINIA='us-east-1'
OREGON='us-west-2'
IRELAND='eu-west-1'
CURRENT_REGION=`aws configure get region`
echo "|"
echo "***********************************************"
echo "******* Configured Region for AWS CLI ********"
if [ "$VIRGINIA" == "$CURRENT_REGION" ]; then
    echo "Working in us-east-1"
elif [ "$OREGON" == "$CURRENT_REGION" ]; then
    echo "Working in us-west-2"
elif [ "$IRELAND" == "$CURRENT_REGION" ]; then
    echo "Working in eu-west-1"
else
    echo "Make sure to configure your AWS CLI to us-east-1, us-west-2, or eu-west-1"
    exit 0
fi
echo "***********************************************"
echo "|"

# Variable Setup
time_stamp=`date "+%H%M%S"`
pid=$$
imc_key_name='imc'${time_stamp}${pid}
#echo $imc_key_name

#. Creating an EC2 Keypair
aws ec2 create-key-pair --key-name ${imc_key_name} > "ec2key_"${imc_key_name}

# Creating service linked role for sitewise
aws iam create-service-linked-role --aws-service-name iotsitewise.amazonaws.com

# Getting VPC ID

vpc_id=`aws ec2 describe-vpcs --region us-east-1 --filters Name=isDefault,Values=true --query Vpcs[].VpcId --output text`
#echo ${vpc_id}
subnet_id=`aws ec2 describe-subnets --filters "Name=vpc-id,Values=${vpc_id}" "Name=availability-zone,Values=us-east-1a" "Name=default-for-az,Values=true" --region=us-east-1 --query Subnets[].SubnetId --output text`
#echo ${subnet_id}
# Creating S3 bucket and uploading files
echo "********* For ALL Templates ***************"
echo "**** EC2 Key info ****"
echo "EC2 Key Pair Name = "${imc_key_name}
echo "***********************************************"
echo "|"
echo "********* For Master Template ***************"
echo "**** Copy and paste the below url for workload cloudformation temaplte ****"
echo "https://aws-quickstart.s3.amazonaws.com/quickstart-tensoriot-industrial-machine-kit/templates/IMC-main.template.yaml"
echo "***********************************************"
echo "|"
echo "********* For Workload Template ***************"
echo "**** Copy and paste the below url for workload cloudformation temaplte ****"
echo "https://aws-quickstart.s3.amazonaws.com/quickstart-tensoriot-industrial-machine-kit/templates/IMC-workload.template.yaml"
echo "***********************************************"
echo "|"
echo "********* For Workload Template ***************"
echo "**** VPC And Subnet information ****"
echo "VPC_ID = "${vpc_id}
echo "SUBNET_ID = "${subnet_id}
echo "***********************************************"