import json
import boto3
import json
import uuid
import time
import argparse
import os

def createQuickSight(boto3Session, awsAccount, s3BucketName, stackName):
    quickSightClient = boto3Session.client('quicksight')
    s3Client = boto3Session.resource('s3')
    imcUUID = str(uuid.uuid4())
    quickSightJson = {
        "fileLocations": [
            {
                "URIPrefixes": [
                    "s3://{}/firehose/2020".format(s3BucketName),
                ]
            }
        ],
        "globalUploadSettings": {}
    }

    with open('/tmp/imcquicksightdata.json', 'w', encoding='utf-8') as manifestFile:
        manifestFile.write(json.dumps(quickSightJson, indent=4))
    s3Object = s3Client.Object(s3BucketName, 'imcquicksightdata.json')
    s3Object.put(Body=json.dumps(quickSightJson))

    response = quickSightClient.list_users(
        AwsAccountId=awsAccount,
        MaxResults=50,
        Namespace='default'
    )
    print(response)

    principalArrayDataSource = []
    principalArrayDataSet = []
    for user in response['UserList']:
        userArn = user['Arn']
        principalInfo = {
            'Principal': userArn,
            'Actions': ["quicksight:DescribeDataSet","quicksight:DescribeDataSetPermissions","quicksight:PassDataSet","quicksight:DescribeIngestion","quicksight:ListIngestions","quicksight:UpdateDataSet","quicksight:DeleteDataSet","quicksight:CreateIngestion","quicksight:CancelIngestion","quicksight:UpdateDataSetPermissions"]
        }
        principalArrayDataSet.append(principalInfo)
        principalInfo = {
            'Principal': userArn,
            'Actions': ["quicksight:DescribeDataSource","quicksight:DescribeDataSourcePermissions","quicksight:PassDataSource","quicksight:UpdateDataSource","quicksight:DeleteDataSource","quicksight:UpdateDataSourcePermissions"]
        }
        principalArrayDataSource.append(principalInfo)

    response = quickSightClient.create_data_source(
        AwsAccountId=awsAccount,
        DataSourceId=imcUUID,
        Name=stackName,
        Type='S3',
        DataSourceParameters={
            'S3Parameters': {
                'ManifestFileLocation': {
                    'Bucket': s3BucketName,
                    'Key': 'imcquicksightdata.json'
                }
            }
        },
        Permissions = principalArrayDataSource
    )
    print(response)
    dataSourceId = response['DataSourceId']
    dataSourceArn = response['Arn']

    response2 = quickSightClient.describe_data_source(
        AwsAccountId=awsAccount,
        DataSourceId=dataSourceId,
    )
    time.sleep(2)

    imcUUID = str(uuid.uuid4())
    print("Going to create dataset")
    print(dataSourceArn)
    response3 = quickSightClient.create_data_set(
        AwsAccountId=awsAccount,
        DataSetId=imcUUID,
        Name=stackName,
        PhysicalTableMap={
            'table1': {
                'S3Source': {
                    'DataSourceArn': dataSourceArn,
                    'InputColumns': [
                        {
                            'Name': 'value',
                            'Type': 'STRING'
                        },
                        {
                            'Name': 'propertyid',
                            'Type': 'STRING'
                        },
                        {
                            'Name': 'timestamp',
                            'Type': 'STRING'
                        },
                        {
                            'Name': 'assetid',
                            'Type': 'STRING'
                        },                                                            
                    ]
                }
            }
        },
        ImportMode='SPICE',
        Permissions=principalArrayDataSet    
    )

    print(response3)

def lambda_handler(event, context):
    boto3Session = boto3
    awsAccount = os.environ['imcawsaccount']
    s3BucketName = os.environ['imcdatabucket']
    stackName = os.environ['stackName']

    createQuickSight(boto3Session, awsAccount, s3BucketName, stackName)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }